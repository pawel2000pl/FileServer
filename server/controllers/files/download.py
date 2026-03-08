import flask
import base64
import datetime
import subprocess
import urllib.parse
from typing import Iterator
from time import sleep, time
from libraries.mime import get_mimetype
from libraries.storage import StorageEntry
from response_stream import ResponseStream, ResponseHeader, ResponseCode, HTTPError
from configuration import BUFFER_SIZE, USE_X_ACCEL_REDIRECT, MAX_DOWNLOAD_RATE, COMPRESSION_TIMEOUT


def get_ranges(r: str, default_size: int) -> tuple[int, int]:
    strs = r.split('-')
    if strs[1] == '':
        i = int(strs[0])
        return (i, default_size)
    return (int(strs[0]), int(strs[1]))


def serve_file(storage_entry: StorageEntry, download: bool = True) -> ResponseStream:

    system_path = storage_entry.get_system_path()
    filename = storage_entry.get_name()
    extension = '.' + filename.rsplit('.', 1)[-1]
    mime = get_mimetype(extension)
    yield ResponseHeader('Content-Type', mime)
    yield ResponseHeader('Content-Disposition', f'attachment; filename="{urllib.parse.quote(filename)}"' if download else 'inline')

    if USE_X_ACCEL_REDIRECT:
        yield ResponseHeader('X-Accel-Redirect', '/storage/' + storage_entry.get_storage_path())
        return

    f = open(system_path, 'rb', 0)
    size = f.seek(0, 2)

    yield ResponseHeader('Cache-Control', None)
    yield ResponseHeader('Pragma', None)
    yield ResponseHeader('Accept-Ranges', 'bytes')
    yield ResponseHeader('Content-Length', str(size))
    if flask.request.method == 'HEAD':
        yield bytes()
        return

    ranges = flask.request.headers.get('Range', f'bytes=0-{size-1}').replace(' ', '')
    raw_ranges = ranges[len('bytes='):]
    ranges_list = list(map(lambda x: tuple(get_ranges(x, size-1)), raw_ranges.split(',')))
    ranges_count = len(ranges_list)
    multipart = ranges_count > 1
    yield ResponseCode(206 if flask.request.headers.get('Range', False) else 200)

    parts = []
    total_size = 0
    boundary = base64.b32encode(open('/dev/urandom', 'rb').read(32)).decode('utf-8') if multipart else str()
    for range_min, range_max in ranges_list:
        if range_max < range_min:
            raise HTTPError(416, 'range_max < range_min')
        if range_max > size:
            yield ResponseHeader('Content-Range', f'bytes /{size}')
            raise HTTPError(416, 'range_max > file_size')
        subheader = f'\r\n--{boundary}\nContent-Type: {mime}\nContent-Range: bytes {range_min}-{range_max}/{size}\r\n\r\n'.encode('utf-8') if multipart else bytes()
        read_size = range_max - range_min + 1
        total_size += len(subheader) + read_size
        parts.append((range_min, range_max, subheader, read_size))
    if multipart:
        yield ResponseHeader('Content-Type', 'multipart/byteranges; boundary='+boundary)
        yield ResponseHeader('Content-Length', str(total_size))
    else:
        yield ResponseHeader('Content-Range', f'bytes {range_min}-{range_max}/{size}')
        yield ResponseHeader('Content-Length', str(parts[0][3]))

    for range_min, range_max, subheader, read_size in parts:
        if multipart:
            yield subheader
        f.seek(range_min)
        while read_size > 0:
            buf = f.read(min(read_size, BUFFER_SIZE))
            read_size -= len(buf)
            sleep(BUFFER_SIZE / MAX_DOWNLOAD_RATE)
            yield buf



def download_partial(storage_entry: StorageEntry, download: bool = False) -> ResponseStream:
    if not storage_entry.read: raise PermissionError()
    assert storage_entry.get_file_view().is_file()
    return serve_file(storage_entry, download)



def download_zipped(entries: list[StorageEntry], download_name: str = 'download') -> ResponseStream:
    if not all(entry.read for entry in entries): raise PermissionError()
    if len(entries) == 0: raise HTTPError(400, 'At least one file is required')
    path = entries[0].get_file_view().path
    if any(entry.get_file_view().path != path for entry in entries): raise HTTPError(400, 'All files must be in the same directory')
    filenames = [entry.get_file_view().name for entry in entries]
    proc = subprocess.Popen(
        ["zip", "-q", "-r", "-"] + filenames,
        cwd=path,
        stdout=subprocess.PIPE
    )
    assert proc.stdout is not None

    timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    filename = download_name + '_' + timestamp_str + '.zip'
    timeout = time() + COMPRESSION_TIMEOUT
    yield ResponseHeader('Content-Disposition', f'attachment; filename="{urllib.parse.quote(filename)}"')
    yield ResponseHeader('Content-Type', 'application/zip')
    try:
        buf = b' '
        while len(buf) and time() < timeout:
            buf = proc.stdout.read(BUFFER_SIZE)
            sleep(BUFFER_SIZE / MAX_DOWNLOAD_RATE)
            yield buf
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.stdout.flush()
                proc.wait(5)
            except subprocess.TimeoutExpired:                
                proc.kill()
                proc.stdout.flush()
                proc.wait(5)
                

