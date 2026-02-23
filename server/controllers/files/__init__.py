import models
import http_utils
from html import escape
from libraries.storage import UrlStorage, StorageEntry
from controllers.common import render_page
from typing import Iterator, Optional, Union
from controllers.files.file import render_file
from controllers.files.backups import render_backups
from controllers.files.download import download_partial
from controllers.files.directory import render_directory
from controllers.shares import render_create_share_form


def content_factory(storage_entry: StorageEntry, **kwargs):
    if not storage_entry.read:
        raise PermissionError()

    yield f'''
        <div class="file-header">
            <span class="file-title">{escape(storage_entry.get_name())}</span>
            <span class="storage-path">{escape(storage_entry.get_name())}</span>
        </div>'''
    yield '<div class="file-tool-panel">'
    if storage_entry.parent is not None and storage_entry.parent.read:
        yield f'''<a class="parent-dir-href" href="{escape(storage_entry.parent.generate_url())}">Go to the parent directory</a>'''
    yield '</div>'    
    
    for s in render_create_share_form(storage_entry):
        yield s

    yield '<br>'
        
    generator = render_directory(storage_entry) if storage_entry.has_entries() else render_file(storage_entry)
    for s in generator:
        yield s

    if storage_entry.can_have_backup():
        yield '<h3>Backups</h3>'
        for s in render_backups(storage_entry):
            yield s



def render_for_token(url_path: list[str], **kwargs) -> Iterator[Union[str, bytes]]:
    storage_entry = UrlStorage(url_path)
    if 'download' in kwargs:
        if not storage_entry.get_file_view().is_file():
            http_utils.error(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, kwargs.get('save', False))
    return render_page(content_factory(storage_entry), **kwargs)
    

def render_for_user(url_path: list[str], **kwargs) -> Iterator[Union[str, bytes]]:
    storage_entry = storage_entry = UrlStorage(url_path)
    if 'download' in kwargs:
        if not storage_entry.get_file_view().is_file():
            http_utils.error(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, kwargs.get('save', False))
    return render_page(content_factory(storage_entry, **kwargs), **kwargs)
    
