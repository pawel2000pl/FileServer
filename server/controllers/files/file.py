import cherrypy
import mimetypes
import configuration
from html import escape
from typing import Iterator
from urllib.parse import quote
from libraries.access import StorageEntry
from controllers.files.backups import render_backups
from controllers.common import format_datetime, format_size


def render_file(storage_entry: StorageEntry, url: str) -> Iterator[str]:
    
    yield f'''        
        <div class="file-header">
            <span class="file-title">{escape(storage_entry.entry.name)}</span>
            <span class="storage-path">{escape(storage_entry.storage_path)}</span>
        </div>'''
    if len(storage_entry.url_path):
        parent_full_path = '/'.join([url] + list(filter(quote, storage_entry.url_path[:-1])))
        yield f'''<a class="parent-dir-href" href="{escape(parent_full_path)}">Go to parent directory</a>'''

    download_url = escape('/'.join([url] + list(filter(quote, storage_entry.url_path)))+'?download=True')

    yield f'<a class="download-btn" href="{download_url}&save=True">Download</a>'

    extension = '.' + storage_entry.entry.name.rsplit('.', 1)[-1]
    mime = mimetypes.types_map.get(extension, 'application/octet-stream')

    yield f'<span class="mime-span">File type: {mime}</span><br>'

    show_new_tab_link = True
    if mime.startswith('text/') or mime == 'application/json' or mime == 'application/xml':
        yield '<textarea class="preview" readonly="readonly">'
        with open(storage_entry.system_path) as f:
            line = ' '
            while len(line) > 0:
                line = f.read(1024)
                yield escape(line)
        yield '</textarea>'
    elif mime.startswith('image/'):
        yield f'<image class="preview" src={download_url} alt="Cannot load the image"/>'
    elif mime.startswith('audio/'):
        yield f'<audio class="preview" controls src="{download_url}"></audio>'
    elif mime.startswith('video/'):
        yield f'<video class="preview" controls src="{download_url}"></video>'
    else:
        show_new_tab_link = False
    if show_new_tab_link:
        yield f'<a class="preview preview-link" target="_blank" href="{download_url}">Open in a new tab</a>'

    if storage_entry.user is not None:
        yield '<h3>Backups</h3>'
        for s in render_backups(storage_entry, url):
            yield s
