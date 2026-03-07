import os
import json
import time
import flask
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
    timestamp = time.time()

    yield '''
        <dialog id="rename_file_panel" class="share-panel">
            <span class="close-modal-btn" onclick="rename_file_panel.close()">Close</span>
            <form action="#" method="post">
                <input id="new_name_name" name="file-name" type="hidden" value="0"/>
                <p>
                    <span>New name</span><br/>
                    <input id="new_name_input" name="new-name" value="Unnamed"/>
                </p>
                <input type="submit" name="rename-file-btn" value="Rename"/>
            </form>
        </dialog>
    '''

    renaming_mode = storage_entry.write and flask.request.method == 'POST' and 'rename-file-btn' in flask.request.form and 'file-name' in flask.request.form and 'new-name' in flask.request.form
    deleting_mode = storage_entry.write and not renaming_mode and flask.request.method == 'POST' and 'delete-file-btn' in flask.request.form and 'confirm-delete' in flask.request.form
    rename_name = flask.request.form.get('file-name', '')
    new_name = flask.request.form.get('new-name', '')

    if renaming_mode and len(rename_name) and len(new_name) and storage_entry.entry_exists(rename_name):
        if storage_entry.entry_exists(new_name):
            yield '<script>alert("Cannot change the name: the file with this name already exists.");</script>'
        else:
            storage_entry.rename_entry(rename_name, new_name, timestamp)

    hide_write_html = '' if storage_entry.write else 'style="display:none;"'

    yield f'''
    <form id="file_list_form" action="#" method="POST">
    <div class="section-div fileslist-div">
        <table id="directory-table" class="content-table dynamic-table file-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th class="main-column dynamic">Name</th>
                    <th {hide_write_html}></th>
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
        name = entry.get_name()
        if deleting_mode and 'file:'+name in flask.request.form:
            storage_entry.remove_entry(name, timestamp)
            continue
        view = entry.get_file_view()
        if view.is_file(): type_str += 'F'
        if view.is_dir(): type_str += 'D'
        if view.is_symlink(): type_str += 'L'
        stat = view.stat()
        count += 1
        full_url = entry.generate_url()
        yield f'''
            <tr>
                <td><input class="file-selector" type="checkbox" name="file:{escape(name)}"/></td>
                <td class="main-column"><a href="{escape(full_url)}">{escape(name)}</a></td>
                <td {hide_write_html}><span style="cursor: pointer" title="Rename" onclick="let s={escape(json.dumps(name))}; new_name_name.value=s;new_name_input.value=s;rename_file_panel.showModal()">&#128394;</span></td>
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
    '''
    if storage_entry.write:
        yield '''
        <p>
            <input id="confirm-delete" type="checkbox" name="confirm-delete" onclick="delete_file_btn.disabled=!event.target.checked;"/>
            <label for="confirm-delete">Confirm deleting</label>
            <br/>
            <input id="delete_file_btn" disabled type="submit" name="delete-file-btn" value="Delete"/>
        </p>
        '''
    yield '''
        <div class="files-legend">
            <span>Legend</span>
            <ul>
                <li>F - file</li>
                <li>D - directory</li>
                <li>L - link (shortcut)</li>
            </ul>
        </div>
    </div>
    </form>
    '''

    yield '''
    '''

