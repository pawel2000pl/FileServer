import os
import configuration
from html import escape
from typing import Iterator
from urllib.parse import quote
from libraries.access import StorageEntry
from libraries.file_view import FileView
from controllers.common import format_datetime, format_size



def __scan_backups(path_prefix: str, path_suffix: str) -> Iterator[FileView]:
    if path_prefix.endswith(os.sep): path_prefix = path_prefix[:-1]
    if path_suffix.startswith(os.sep): path_suffix = path_suffix[1:]
    
    while True:
        if not path_prefix.endswith(os.sep + '.') and os.sep in path_prefix and os.path.isdir(path_prefix):
            for entry in os.scandir(path_prefix):
                if not entry.name.startswith(configuration.BACKUP_PREFIX): continue
                if path_suffix.startswith(entry.name+os.sep): continue
                if path_suffix == entry.name: continue
                if not entry.is_dir(): continue
                backup_file = entry.path + os.sep + path_suffix
                if not os.path.exists(backup_file): continue
                yield FileView(backup_file)
                for subentry in __scan_backups(entry.path, path_suffix):
                    yield subentry
        pos = path_suffix.find(os.sep)
        if pos < 0: break
        path_prefix += os.sep + path_suffix[:pos]
        path_suffix = path_suffix[pos+1:]


def scan_backups(storage_entry: StorageEntry) -> Iterator[StorageEntry]:
    shortest_storage_path = storage_entry.shortest_storage_path(False)
    assert storage_entry.storage_path.startswith(shortest_storage_path)
    base_path = FileView.absolute_filename(configuration.STORAGE_PATH) + os.sep
    base_search_path = FileView.absolute_filename(base_path + shortest_storage_path)+os.sep
    search_path = storage_entry.storage_path[len(shortest_storage_path):]
    for entry in __scan_backups(base_search_path, search_path):
        fspath = entry.__fspath__()
        assert fspath.startswith(base_search_path)
        url_path = fspath[len(base_search_path):].split(os.sep)
        storage_path = fspath[len(base_path):]
        yield StorageEntry(url_path, storage_path, fspath, entry, True, False, user=storage_entry.user, token=storage_entry.token)


def render_backups(storage_entry: StorageEntry, url: str) -> Iterator[str]:
    yield f'''
    <div class="section-div fileslist-div">
        <table class="content-table file-table">
            <thead>
                <tr>
                    <th class="main-column">Path</th>
                    <th>Modified</th>
                    <th>Size</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
    '''
    count = 0
    for entry in scan_backups(storage_entry):
        type_str = ''
        if entry.entry.is_file(): type_str += 'F'
        if entry.entry.is_dir(): type_str += 'D'
        if entry.entry.is_symlink(): type_str += 'S'
        stat = entry.entry.stat()
        count += 1
        url_str = os.sep.join(entry.url_path)
        full_url = '/'.join([url] + entry.url_path)
        yield f'''
            <tr>
                <th class="main-column"><a href="{escape(full_url)}">{escape(url_str)}</a></th>
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
        base_url = list(filter(lambda s: not s.startswith(configuration.BACKUP_PREFIX), storage_entry.url_path))
        if len(base_url) != len(storage_entry.url_path):
            if len(base_url) == 0:
                yield f'''
                    <span class="backup-warning"><a href="{escape(url)}">You are watching backups of backup of your main directory. Click here so go to your main directory.</a></span>
                '''
            else:
                base_storage: StorageEntry
                if storage_entry.user is not None:
                    base_storage = storage_entry.from_user(storage_entry.user, base_url)
                elif storage_entry.token is not None:
                    base_storage = storage_entry.from_token(storage_entry.token, base_url)
                else:
                    assert False
                if base_storage.entry.exists():
                    full_url = '/'.join([url] + list(filter(quote, base_url)))
                    yield f'''
                        <span class="backup-warning"><a href="{escape(full_url)}">You are watching backups of backup. Click here to watch the main file.</a></span>
                    '''
    except (PermissionError, FileNotFoundError):
        pass

