import flask
import models
from html import escape
from controllers.common import render_page
from typing import Iterator, Optional, Union
from response_stream import ResponseStream, HTTPError
from libraries.storage import UrlStorage, StorageEntry

from controllers.files.file import render_file
from controllers.files.backups import render_backups
from controllers.shares import render_create_share_for
from controllers.files.download import download_partial
from controllers.files.directory import render_directory


def content_factory(storage_entry: StorageEntry) -> Iterator[str]:
    if not storage_entry.read:
        raise PermissionError()

    create_share_generator = render_create_share_for(storage_entry)
    directory_generator = render_directory(storage_entry) if storage_entry.has_entries() else render_file(storage_entry)
    backups_generator = render_backups(storage_entry) if storage_entry.can_have_backup() else []
    url = storage_entry.generate_url()
    path_htmls = []
    se: Optional[StorageEntry] = storage_entry
    while se is not None and se.has_name():
        path_htmls.append(f'<a href={escape(se.generate_url())}>{escape(se.get_name())}</a>')
        se = se.parent
    path_html = '/'.join(path_htmls[::-1][1:])

    yield f'''
        <div class="file-header">
            <span class="file-title">{escape(storage_entry.get_name())}</span>
            <span class="storage-path">{path_html}</span>
        </div>'''
    yield '<div class="file-tool-panel">'
    if storage_entry.parent is not None and storage_entry.parent.read:
        yield f'''<a class="parent-dir-href" href="{escape(storage_entry.parent.generate_url())}">Go to the parent directory</a>'''
    yield '</div>'

    for s in create_share_generator:
        yield s

    yield '<br>'

    for s in directory_generator:
        yield s

    if storage_entry.can_have_backup():
        yield '<h3>Backups</h3>'
        for s in backups_generator:
            yield s


def render_for_token(url_path: list[str]) -> ResponseStream:
    storage_entry = UrlStorage(url_path)
    if 'download' in flask.request.args:
        if not storage_entry.get_file_view().is_file():
            raise HTTPError(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, bool(flask.request.args.get('save', False)))
    return render_page(content_factory(storage_entry))


def render_for_user(url_path: list[str]) -> ResponseStream:
    storage_entry = UrlStorage(url_path)
    if 'download' in flask.request.args:
        if not storage_entry.get_file_view().is_file():
            raise HTTPError(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, bool(flask.request.args.get('save', False)))
    return render_page(content_factory(storage_entry))

