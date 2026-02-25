import os
import configuration
from html import escape
from typing import Iterator
from urllib.parse import quote
from libraries.file_view import FileView
from libraries.storage import StorageEntry
from controllers.common import format_datetime, format_size


def render_backups(storage_entry: StorageEntry) -> Iterator[str]:

    scanner = storage_entry.scan_backups()

    yield f'''
    <div class="section-div fileslist-div">
        <table class="content-table file-table">
            <thead>
                <tr>
                    <th class="main-column">Path</th>
                    <th class="only-pc">Modified</th>
                    <th class="only-pc">Size</th>
                    <th class="only-pc">Type</th>
                </tr>
            </thead>
            <tbody>
    '''
    count = 0
    for entry in scanner:
        type_str = ''
        view = entry.get_file_view()
        if view.is_file(): type_str += 'F'
        if view.is_dir(): type_str += 'D'
        if view.is_symlink(): type_str += 'S'
        stat = view.stat()
        count += 1
        url_str = entry.generate_url()
        show_url = '/'.join(url_str.split('/')[3:])
        yield f'''
            <tr>
                <td class="main-column"><a href="{escape(url_str)}">{escape(show_url)}</a></td>
                <td class="only-pc">{escape(format_datetime(stat.st_mtime))}</td>
                <td class="only-pc" sortkey="{int(stat.st_size)}">{format_size(stat.st_size)}</td>
                <td class="only-pc">{escape(type_str)}</td>
            </tr>
        '''

    yield f'''
          </tbody>
        </table>
        <div class="fileslist-summary">
            Total: {count} backups.
        </div>
    </div>
    '''


    try:
        if storage_entry.path_is_backup():
            newest = storage_entry.entry_no_backup()
            full_url = newest.generate_url()
            yield f'''
                <span class="backup-warning"><a href="{escape(full_url)}">You are watching backups of backup. Click here to watch the main file.</a></span>
            '''
    except (PermissionError, FileNotFoundError):
        pass

