import os
import models
import configuration
from html import escape
from urllib.parse import quote
from libraries.file_view import FileView
from libraries.storage import StorageEntry
from typing import Iterator, Union, Optional
from controllers.common import format_datetime, format_size


def render_directory(storage_entry: StorageEntry) -> Iterator[str]:

    base_url = storage_entry.generate_url()

    yield f'''
    <div class="section-div fileslist-div">
        <table id="directory-table" class="content-table dynamic-table file-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th class="main-column dynamic">Name</th>
                    <th class="only-pc dynamic">Modified</th>
                    <th class="only-pc dynamic">Size</th>
                    <th class="only-pc dynamic">Type</th>
                </tr>
            </thead>
            <tbody>
    '''

    count = 0

    for entry in storage_entry.scan_entries():
        type_str = ''
        if entry.is_file(): type_str += 'F'
        if entry.is_dir(): type_str += 'D'
        if entry.is_symlink(): type_str += 'L'
        stat = entry.stat()
        count += 1
        full_url = base_url + '/' + quote(entry.name)
        yield f'''
            <tr>
                <td><input type="checkbox" name="fileentry[]" value="{escape(full_url)}"/></td>
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
        <div class="files-legend">
            <span>Legend</span>
            <ul>
                <li>F - file</li>
                <li>D - directory</li>
                <li>L - link (shortcut)</li>
            </ul>
        </div>
    </div>
    '''

