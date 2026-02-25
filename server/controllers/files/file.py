import configuration
from html import escape
from typing import Iterator
from urllib.parse import quote
from libraries.mime import get_mimetype
from libraries.storage import StorageEntry
from controllers.common import format_datetime, format_size


def render_file(storage_entry: StorageEntry) -> Iterator[str]:
    
    download_url = storage_entry.generate_url()+'?download=True'
    system_path = storage_entry.get_system_path()
    extension = storage_entry.get_name().rsplit('.', 1)[-1]
    mime = get_mimetype(extension)

    yield f'<a class="download-btn" href="{download_url}&save=True">Download</a>'
    yield f'<span class="mime-span">File type: {mime}</span><br>'

    show_new_tab_link = True
    if mime.startswith('text/') or mime == 'application/json' or mime == 'application/xml':
        yield '<textarea class="preview" readonly="readonly">'
        with open(system_path) as f:
            line = ' '
            while len(line) > 0:
                line = f.read(1024)
                yield escape(line)
        yield '</textarea>'
    elif mime.startswith('image/'):
        yield f'<image class="preview" src="{download_url}" alt="Cannot load the image"/>'
    elif mime.startswith('audio/'):
        yield f'<audio class="preview" controls src="{download_url}"></audio>'
    elif mime.startswith('video/'):
        yield f'<video class="preview" controls src="{download_url}"></video>'
    else:
        show_new_tab_link = False
    if show_new_tab_link:
        yield f'<a class="preview preview-link" target="_blank" href="{download_url}">Open in a new tab</a>'
