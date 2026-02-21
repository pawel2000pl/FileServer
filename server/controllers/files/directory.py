import os
import models
import cherrypy
import configuration
from html import escape
from urllib.parse import quote
from libraries.file_view import FileView
from libraries.access import StorageEntry
from typing import Iterator, Union, Optional
from controllers.files.backups import render_backups
from controllers.common import format_datetime, format_size


def render_directory(storage_entry: Optional[StorageEntry], url: str) -> Iterator[str]:
    assert storage_entry is None or storage_entry.entry.is_dir()
    user_id = cherrypy.session.get('user_id', None)
    if user_id is None: raise PermissionError()
    user = models.User(id=user_id)
    if storage_entry is None:
        yield f'''
            <div>
                <span class="file-title">Files of {escape(user.name)}</span>
            </div>'''
    else:
        yield f'''
            <div>
                <span class="file-title">{escape(storage_entry.entry.name)}</span>
                <span class="storage-path">{escape(storage_entry.storage_path)}</span>
            </div>'''
    if storage_entry is not None and len(storage_entry.url_path) > 0:
        parent_full_path = full_url = '/'.join([url] + storage_entry.url_path[:-1])
        yield f'''<a class="parent-dir-href" href="{escape(parent_full_path)}">Go to parent directory</a>'''
    yield f'''
    <div class="section-div fileslist-div">
        <table class="content-table file-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th class="main-column">Name</th>
                    <th>Modified</th>
                    <th>Size</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
    '''

    count = 0
    initial_storage_path = [] if storage_entry is None else storage_entry.url_path
    scanner: Iterator[Union[FileView, os.DirEntry]]
    if storage_entry is None:
        query = models.Capability.query()
        query.where('user', user)
        query.where_not_null('name')
        scanner = (FileView(configuration.STORAGE_PATH+os.sep+cap.storage_path) for cap in query.get())
    else:
        scanner = os.scandir(storage_entry.system_path)

    for entry in scanner:
        type_str = ''
        if entry.is_file(): type_str += 'F'
        if entry.is_dir(): type_str += 'D'
        if entry.is_symlink(): type_str += 'S'
        stat = entry.stat()
        count += 1
        full_url = '/'.join([url] + list(filter(quote, initial_storage_path + [entry.name])))
        yield f'''
            <tr>
                <th><input type="checkbox" name="fileentry" value="{escape(full_url)}"/></th>
                <td class="main-column"><a href="{escape(full_url)}">{escape(entry.name)}</a></td>
                <td class="only-pc">{escape(format_datetime(stat.st_mtime))}</td>
                <td class="only-pc" sortkey="{int(stat.st_size)}">{format_size(stat.st_size)}</td>
                <td class="only-pc">{escape(type_str)}</td>
            </tr>
        '''

    yield f'''
          </tbody>
        </table>
        <div class="fileslist-summary">
            Total: {count} elements.
        </div>
    </div>
    '''

    if storage_entry is not None and storage_entry.user is not None:
        yield '<h3>Backups</h3>'
        for s in render_backups(storage_entry, url):
            yield s

