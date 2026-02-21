import cherrypy
import configuration
from html import escape
from typing import Iterator
from urllib.parse import quote
from libraries.access import StorageEntry
from controllers.files.backups import render_backups
from controllers.common import format_datetime, format_size


def render_file(storage_entry: StorageEntry, url: str) -> Iterator[str]:
    
    yield f'''        
        <div>
            <span class="file-title">{escape(storage_entry.entry.name)}</span>
            <span class="storage-path">{escape(storage_entry.storage_path)}</span>
        </div>'''
    if len(storage_entry.url_path):
        parent_full_path = full_url = '/'.join([url] + list(filter(quote, storage_entry.url_path[:-1])))
        yield f'''<a class="parent-dir-href" href="{escape(parent_full_path)}">Go to parent directory</a>'''

    if storage_entry.user is not None:
        yield '<h3>Backups</h3>'
        for s in render_backups(storage_entry, url):
            yield s
