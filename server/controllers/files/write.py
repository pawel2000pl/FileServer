import os
import json
import flask
import base64
import shutil
import tempfile
import configuration
from time import time
from html import escape
from typing import Iterator
from threading import Thread
from models import Capability
from libraries.file_view import FileView
from libraries.filename import assert_filename
from controllers.common import add_notification
from libraries.storage import StorageEntry, UrlStorage


def render_write(entry: StorageEntry) -> Iterator[str]:
    if not entry.has_entries():
        yield ''
        return

    if configuration.ALLOW_LINKS:
        yield '''
            <span class="link-like-button" title="Copy links" onclick="getSelected('copy-links')">Copy as links</span>
        '''

    yield '''
        <span class="link-like-button" title="Copy selected" onclick="getSelected('copy')">Copy</span>
        <script>
            function getSelected(operation) {
                const file_list = Array.from(document.querySelectorAll('input[class="file-selector"]:checked')).map(checkbox => checkbox.name.substr(5));
                const url_path = %s;
                const data = {
                    operation: operation,
                    url_path: url_path,
                    file_list: file_list
                };
                localStorage.setItem('clipboard', JSON.stringify(data));
            }
        </script>
    ''' % json.dumps(entry.urlpath)

    if not entry.write:
        yield ''
        return

    yield '''
        <span class="link-like-button" title="Cut selected" onclick="getSelected('cut')">Cut</span>
        <span class="link-like-button" title="Paste" onclick="pasteFiles()">Paste</span>
        <script>
            function pasteFiles() {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'paste-data';
                input.value = localStorage.getItem('clipboard');
                file_list_form.appendChild(input);
                file_list_form.submit();
            }
        </script>
    '''


    if flask.request.method == 'POST' and 'paste-data' in flask.request.form:
        paste_data_str = flask.request.form['paste-data']
        user_id = flask.session.get('user_id', None)
        def worker():
            try:
                data = json.loads(paste_data_str)
                operation = data['operation']
                source_entry = UrlStorage(data['url_path'])
                add_notification(f'Started operation "{operation}" on files: "{source_entry.get_name()}/..." -> "{entry.get_name()}"/...', user_id)
                if operation == 'cut' and not source_entry.write: raise PermissionError()
                for name in data['file_list']:
                    if not source_entry.entry_exists(name):
                        raise FileNotFoundError()
                    if entry.entry_exists(name):
                        raise FileExistsError()

                timestamp = time()
                for name in data['file_list']:
                    if operation == 'cut':
                        entry.move_entry(source_entry, name, name, timestamp)
                    elif operation == 'copy-links':
                        entry.add_entry(name, source_entry.goto(name).get_system_path(), timestamp, options='LINK')
                    elif operation == 'copy':
                        entry.add_entry(name, source_entry.goto(name).get_system_path(), timestamp, options='NONE')                
                    yield f'<!-- Entry "{escape(name)}" has been saved successfully -->'

                add_notification(f'Finished working with files: "{source_entry.get_name()}/..." -> "{entry.get_name()}/..."', user_id)
            except FileExistsError:
                add_notification("Cannot paste: at least one source file has the same name as an existsed file in the destination.", user_id)
            except PermissionError:
                add_notification("Cannot paste: you have no access for removing files from destination.", user_id)
            except FileNotFoundError:
                add_notification("Cannot paste: at least one source file does not exist.", user_id)
            except shutil.Error:
                add_notification("Cannot paste: maybe you tried to move a directory into itself.", user_id)
            except:
                add_notification("Cannot paste: invalid request.", user_id)

        thread = Thread(target=worker)
        thread.start()
        thread.join(configuration.ASYNC_MIN_TIME)

    yield '''
        <span class="link-like-button" onclick="file_upload_dialog.showModal()">Upload</span>
        <dialog id="file_upload_dialog">
            <span class="close-modal-btn" onclick="file_upload_dialog.close()">Close</span>
            <form action="#" method="POST" enctype="multipart/form-data">
                <p style="text-wrap: nowrap;">
                    <button onclick="event.preventDefault(); file_picker.click();">Select files...</button>
                    <span id="selected_files_count">No files selected</span>
                    <input id="file_picker" style="display:none;" type="file" name="files" multiple onchange="
                        if (file_picker.files.length == 0)
                            selected_files_count.textContent = 'No files selected';
                        else if (file_picker.files.length == 1)
                            selected_files_count.textContent = 'Selected 1 file';
                        else
                            selected_files_count.textContent = `Selected ${file_picker.files.length} files`;
                    " />
                    <br/>
                    <input id="overwrite" type="checkbox" name="overwrite" checked/>
                    <label for="overwrite">Overwrite</label>
                </p>
                <input type="submit" name="file-upload" value="Upload" />
            </form>
        </dialog>
    '''

    yield '''
        <span class="link-like-button" onclick="new_directory_file_panel.showModal()">Create a new directory</span>
        <dialog id="new_directory_file_panel" class="share-panel">
            <span class="close-modal-btn" onclick="new_directory_file_panel.close()">Close</span>
            <form action="#" method="post">
                <p>
                    <span>Name</span><br/>
                    <input name="new-name" value="Unnamed"/>
                </p>
                <input type="submit" name="new-directory-btn" value="Create"/>
            </form>
        </dialog>
    '''

    entry_system_path = entry.get_system_path()

    if flask.request.method == 'POST' and 'new-directory-btn' in flask.request.form and 'new-name' in flask.request.form:
        new_name = flask.request.form['new-name']
        try:
            assert_filename(new_name)
            if entry.entry_exists(new_name): raise FileExistsError()
            new_dir = entry_system_path + os.sep + new_name
            os.mkdir(new_dir)
        except FileExistsError:
            add_notification("Cannot create a directory: there is already a file or a directory with the same name.", user_id)
        except PermissionError:
            add_notification("Cannot create a directory: invalid name", user_id)
        except:
            add_notification("Cannot create a directory: invalid request.", user_id)


    if 'file-upload' in flask.request.form:
        overwrite = 'overwrite' in flask.request.form
        timestamp = time()
        for file in flask.request.files.getlist("files"):
            filename = file.filename
            if filename is None: continue
            if filename == '': continue
            assert_filename(filename)
            i = 2
            original_filename = filename
            while not overwrite and entry.entry_exists(filename):
                parts = original_filename.rsplit('.', 1)
                filename = parts[0] + '(%d)'%i
                if len(parts) > 1: filename += '.' + parts[1]
                i += 1
            
            if isinstance(file.stream, tempfile._TemporaryFileWrapper):
                entry.add_entry(filename, file.stream.name, timestamp, 'MOVE')
            else:
                temp_filename = entry_system_path + os.sep + base64.b32encode(open('/dev/urandom', 'rb').read(32)).decode('utf-8')
                file.save(temp_filename)
                entry.add_entry(filename, temp_filename, timestamp, 'MOVE')
            yield f'<!-- File "{escape(filename)}" has been saved successfully -->'



