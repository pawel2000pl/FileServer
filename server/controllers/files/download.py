import base64
import mimetypes
import http_utils
import urllib.parse
from typing import Iterator
from itertools import chain
from libraries.storage import StorageEntry
from controllers.files.stream_zip import stream_zip
from configuration import DEFAULT_RANGE_SIZE, FILE_BUFFER_SIZE


def get_ranges(r: str, default_size: int, max_range: int) -> tuple[int, int]:
    strs = r.split('-')
    if strs[1] == '':
        i = int(strs[0])
        return (i, min(max_range, i+default_size))
    return (int(strs[0]), int(strs[1]))


def serve_file(system_path: str, filename: str, download: bool = True, default_size: int = DEFAULT_RANGE_SIZE) -> Iterator[bytes]:    

    f = open(system_path, 'rb', 0)
    size = f.seek(0, 2)

    extension = '.' + filename.rsplit('.', 1)[-1]
    mime = mimetypes.types_map.get(extension, 'application/octet-stream')
    http_utils.enable_custom_content_type()
    
    http_utils.enable_stream()

    http_utils.set_response_header('Cache-Control', None)
    http_utils.set_response_header('Pragma', None)
    http_utils.set_response_header('Accept-Ranges', 'bytes')
    http_utils.set_response_header('Content-Length', str(size))
    http_utils.set_response_header('Custom-Content-Type', mime)
    http_utils.set_response_header('Content-Disposition', f'attachment; filename="{urllib.parse.quote(filename)}"' if download else 'inline')
    if http_utils.get_request_method() == 'HEAD':
        yield bytes()
        return
        
    ranges = http_utils.get_request_header('Range', f'bytes=0-{size-1}').replace(' ', '')
    raw_ranges = ranges[len('bytes='):]
    ranges_list = list(map(lambda x: tuple(get_ranges(x, default_size, size-1)), raw_ranges.split(',')))
    ranges_count = len(ranges_list)
    multipart = ranges_count > 1
    http_utils.set_status_code(206 if http_utils.get_request_header('Range', False) else 200)

    parts = []
    total_size = 0
    boundary = base64.b32encode(open('/dev/urandom', 'rb').read(32)).decode('utf-8') if multipart else str()
    for range_min, range_max in ranges_list:
        if range_max < range_min:
            http_utils.error(416, 'range_max < range_min')
        if range_max > size:
            http_utils.set_response_header('Content-Range', f'bytes /{size}')
            http_utils.error(416, 'range_max > file_size')
        subheader = f'\r\n--{boundary}\nContent-Type: {mime}\nContent-Range: bytes {range_min}-{range_max}/{size}\r\n\r\n'.encode('utf-8') if multipart else bytes()
        read_size = range_max - range_min + 1
        total_size += len(subheader) + read_size
        parts.append((range_min, range_max, subheader, read_size))
    if multipart:
        http_utils.set_response_header('Custom-Content-Type', 'multipart/byteranges; boundary='+boundary)
        http_utils.set_response_header('Content-Length', str(total_size))
    else:
        http_utils.set_response_header('Content-Range', f'bytes {range_min}-{range_max}/{size}')
        http_utils.set_response_header('Content-Length', str(parts[0][3]))

    for range_min, range_max, subheader, read_size in parts:
        if multipart:
            yield subheader
        f.seek(range_min)        
        while read_size > 0:
            buf = f.read(min(read_size, FILE_BUFFER_SIZE))
            read_size -= len(buf)
            yield buf



def download_partial(storage_entry: StorageEntry, download: bool = False) -> Iterator[bytes]:
    assert storage_entry.get_file_entry().is_file()
    return serve_file(storage_entry.get_system_path(), storage_entry.get_name(), download)
    

