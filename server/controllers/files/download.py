import base64
import cherrypy
import mimetypes
import urllib.parse
from typing import Iterator
from libraries.access import StorageEntry
from controllers.files.stream_zip import stream_zip


def enable_custom_content_type():
    headers = cherrypy.response.headers
    original_encode = headers.encode
    def new_encode(*args, **kwargs):
        if 'Custom-Content-Type' in headers:
            headers['Content-Type'] = headers['Custom-Content-Type']
            headers.pop('Custom-Content-Type')
        return original_encode(*args, **kwargs)
    headers.encode = new_encode


def serve_file(system_path: str, filename: str, download: bool = True) -> Iterator[bytes]:    
    f = open(system_path, 'rb')
    size = f.seek(0, 2)
    extension = '.' + filename.rsplit('.', 1)[-1]
    mime = mimetypes.types_map.get(extension, 'application/octet-stream')
    enable_custom_content_type()

    if 'Cache-Control' in cherrypy.response.headers: cherrypy.response.headers.pop('Cache-Control')
    if 'Pragma' in cherrypy.response.headers: cherrypy.response.headers.pop('Pragma')
    cherrypy.response.headers['Accept-Ranges'] = 'bytes'
    cherrypy.response.headers['Content-Length'] = size
    cherrypy.response.headers['Custom-Content-Type'] = mime
    cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(filename)}"' if download else 'inline'
    if cherrypy.request.method == 'HEAD':
        yield bytes()
        return
        
    cherrypy.response.stream = True
    ranges = cherrypy.request.headers.get('Range', f'bytes=0-{size-1}').replace(' ', '')
    raw_ranges = ranges[len('bytes='):]
    ranges_list = list(map(lambda x: tuple(map(int, x.split('-', 2))), raw_ranges.split(',')))
    ranges_count = len(ranges_list)
    multipart = ranges_count > 1
    cherrypy.response.status = 206 if cherrypy.request.headers.get('Range', False) else 200

    parts = []
    total_size = 0
    boundary = base64.b32encode(open('/dev/urandom', 'rb').read(32)).decode('utf-8') if multipart else str()
    for range_min, range_max in ranges_list:
        if range_max < range_min:
            raise cherrypy.HTTPError(416, 'range_max < range_min')
        if range_max > size:
            cherrypy.response.headers['Content-Range'] = f'bytes /{size}'
            raise cherrypy.HTTPError(416, 'range_max > file_size')
        subheader = f'\r\n--{boundary}\nContent-Type: {mime}\nContent-Range: bytes {range_min}-{range_max}/{size}\r\n\r\n'.encode('utf-8') if multipart else bytes()
        read_size = range_max - range_min + 1
        total_size += len(subheader) + read_size
        parts.append((range_min, range_max, subheader, read_size))
    if multipart:
        cherrypy.response.headers['Custom-Content-Type'] = 'multipart/byteranges; boundary='+boundary
        cherrypy.response.headers['Content-Length'] = total_size
    else:
        cherrypy.response.headers['Content-Range'] = f'bytes {range_min}-{range_max}/{size}'
        cherrypy.response.headers['Content-Length'] = parts[0][3]

    for range_min, range_max, subheader, read_size in parts:
        if multipart:
            yield subheader
        f.seek(range_min)
        while read_size > 0:
            buf = f.read(min(read_size, 65536))
            read_size -= len(buf)
            yield buf



def download_partial(storage_entry: StorageEntry, download: bool = False) -> Iterator[bytes]:
    assert storage_entry.entry.is_file()
    return serve_file(storage_entry.system_path, storage_entry.entry.name, download)



