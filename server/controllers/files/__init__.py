import flask
import models
from html import escape
from controllers.common import render_page
from typing import Iterator, Optional, Union
from response_stream import ResponseStream, HTTPError
from libraries.storage import UrlStorage, StorageEntry

from controllers.files.file import render_file
from controllers.files.write import render_write
from controllers.files.backups import render_backups
from controllers.shares import render_create_share_for
from controllers.files.download import download_partial, download_zipped
from controllers.files.directory import render_directory, render_download_options


def content_factory(storage_entry: StorageEntry) -> Iterator[str]:
    if not storage_entry.read:
        raise PermissionError()

    create_share_generator = render_create_share_for(storage_entry)
    write_generator = render_write(storage_entry)
    download_generator = render_download_options(storage_entry)
    directory_generator = render_directory(storage_entry) if storage_entry.has_entries() else render_file(storage_entry)
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
        for s in download_generator:
            yield s
        for s in write_generator:
            yield s
        for s in create_share_generator:
            yield s
    yield '</div>'

    yield '<br/>'

    for s in directory_generator:
        yield s

    if storage_entry.can_have_backup():
        try:
            backups_generator = render_backups(storage_entry)
            yield '<h3>Backups</h3>'
            for s in backups_generator:
                yield s
        except (PermissionError, NotImplementedError, FileNotFoundError):
            pass



def make_request(url_path: list[str]) -> ResponseStream:
    storage_entry = UrlStorage(url_path)
    if 'download' in flask.request.args:
        if not storage_entry.get_file_view().is_file():
            raise HTTPError(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, bool(flask.request.args.get('save', False)))
    if flask.request.method == 'POST' and 'download-action' in flask.request.form:
        if storage_entry.get_file_view().is_dir() and 'download-directory' in flask.request.form:
            return download_zipped([storage_entry])
        file_list = [storage_entry.goto(name[5:]) for name in flask.request.form.keys() if name.startswith('file:')]
        if len(file_list) > 0:
            if len(file_list) == 1 and file_list[0].get_file_view().is_file():
                return download_partial(file_list[0], True)
            return download_zipped(file_list)
    return render_page(content_factory(storage_entry))

