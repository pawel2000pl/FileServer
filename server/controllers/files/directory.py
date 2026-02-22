import os
import models
import cherrypy
import configuration
from html import escape
from urllib.parse import quote
from libraries.file_view import FileView
from libraries.storage import StorageEntry
from typing import Iterator, Union, Optional
from controllers.common import format_datetime, format_size


def render_directory(storage_entry: StorageEntry) -> Iterator[str]:


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
    base_url = storage_entry.generate_url()

    for entry in storage_entry.scan_entries():
        type_str = ''
        if entry.is_file(): type_str += 'F'
        if entry.is_dir(): type_str += 'D'
        if entry.is_symlink(): type_str += 'S'
        stat = entry.stat()
        count += 1
        full_url = base_url + '/' + quote(entry.name)
        yield f'''
            <tr>
                <th><input type="checkbox" name="fileentry[]" value="{escape(full_url)}"/></th>
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
        <p>
            <p>Legend</p>
            <ul>
                <li>F - file</li>
                <li>D - directory</li>
                <li>L - link (shortcut)</li>
            </ul>
        </p>
    </div>
    '''

