import os
import flask
import base64
from time import time
from html import escape
from typing import Iterator
from models import Capability
from libraries.file_view import FileView
from libraries.storage import StorageEntry


def render_write(entry: StorageEntry) -> Iterator[str]:
    if not entry.write or not entry.has_entries():
        yield ''
        return

    yield f'''
        <span class="link-like-button" onclick="file_upload_dialog.showModal()">Upload</span>
        <dialog id="file_upload_dialog">
            <span class="close-modal-btn" onclick="file_upload_dialog.close()">Close</span>
            <form action="#" method="POST" enctype="multipart/form-data">
                <p>
                    <input type="file" name="files" multiple />
                    <br/>
                    <input id="overwrite" type="checkbox" name="overwrite" checked/>
                    <label for="overwrite">Overwrite</label>
                </p>
                <input type="submit" name="file-upload" value="Upload" />
            </form>
        </dialog>
    '''

    entry_system_path = entry.get_system_path()

    if 'file-upload' in flask.request.form:
        overwrite = 'overwrite' in flask.request.form
        timestamp = time()
        for file in flask.request.files.getlist("files"):
            filename = file.filename
            if filename is None: continue
            if filename == '': continue
            if len({'/', '\\', '~', ':'}.intersection(filename)): continue
            if filename in {'..', '.', '~'}: continue
            i = 2
            original_filename = filename
            while not overwrite and entry.entry_exists(filename):
                parts = original_filename.rsplit('.', 1)
                filename = parts[0] + '(%d)'%i
                if len(parts) > 1: filename += '.' + parts[1]
                i += 1
            temp_filename = entry_system_path + os.sep + base64.b32encode(open('/dev/urandom', 'rb').read(32)).decode('utf-8')
            file.save(temp_filename)
            entry.add_entry(filename, temp_filename, timestamp)




