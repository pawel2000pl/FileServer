import base64
import flask
import mimetypes
import urllib.parse
from typing import Iterator
from itertools import chain
from libraries.storage import StorageEntry
from configuration import BUFFER_SIZE
from controllers.files.stream_zip import stream_zip
from response_stream import ResponseStream, ResponseHeader, ResponseCode, HTTPError


def get_ranges(r: str, default_size: int) -> tuple[int, int]:
    strs = r.split('-')
    if strs[1] == '':
        i = int(strs[0])
        return (i, default_size)
    return (int(strs[0]), int(strs[1]))


def serve_file(system_path: str, filename: str, download: bool = True) -> ResponseStream:

    f = open(system_path, 'rb', 0)
    size = f.seek(0, 2)

    extension = '.' + filename.rsplit('.', 1)[-1]
    mime = mimetypes.types_map.get(extension, 'application/octet-stream')

    yield ResponseHeader('Cache-Control', None)
    yield ResponseHeader('Pragma', None)
    yield ResponseHeader('Accept-Ranges', 'bytes')
    yield ResponseHeader('Content-Length', str(size))
    yield ResponseHeader('Custom-Content-Type', mime)
    yield ResponseHeader('Content-Disposition', f'attachment; filename="{urllib.parse.quote(filename)}"' if download else 'inline')
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
        yield ResponseHeader('Custom-Content-Type', 'multipart/byteranges; boundary='+boundary)
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
            yield buf



def download_partial(storage_entry: StorageEntry, download: bool = False) -> ResponseStream:
    assert storage_entry.get_file_view().is_file()
    return serve_file(storage_entry.get_system_path(), storage_entry.get_name(), download)


