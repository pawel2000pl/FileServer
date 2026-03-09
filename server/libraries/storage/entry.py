import os
import shutil
import datetime
import configuration
from time import time
from os import DirEntry
from urllib.parse import quote
from libraries.file_view import FileView
from libraries.file_loop import is_filesystem_loop
from typing import Optional, Iterator, Union, Literal
from configuration import ALLOW_LINKS, BACKUP_PREFIX, SHOW_BACKUPS_IN_FILES


class StorageEntry:

    def __init__(self, parent: Optional['StorageEntry'], urlpath: list[str], fileview: Union[DirEntry, FileView, None] = None, **kwargs):
        assert fileview is None or isinstance(fileview, (FileView, DirEntry))
        self.parent = parent
        self.urlpath = urlpath
        self.read = False
        self.write = False        
        self.__file_view: Union[FileView, DirEntry, None] = fileview
        self.__cached_url: Optional[str] = None

    
    def get_name(self) -> str:
        if not self.has_name():
            raise PermissionError()
        return self.urlpath[-1]

    
    def has_name(self) -> bool:
        return len(self.urlpath) > 0


    def is_backup(self) -> bool:
        return self.get_name().startswith(configuration.BACKUP_PREFIX)


    def can_have_backup(self) -> bool:
        return True


    def can_be_shared(self) -> bool:
        return self.is_real_file()


    def is_real_file(self) -> bool:
        try:
            self.get_storage_path()
            return True
        except NotImplementedError:
            return False


    def path_is_backup(self) -> bool:
        return self.is_backup() or (self.parent is not None and self.parent.path_is_backup())


    def entry_no_backup(self) -> 'StorageEntry':
        names = []
        cur = self
        while cur.parent is not None and cur.parent.read:
            names.append(cur.get_name())
            cur = cur.parent
        names.reverse()
        for name in names:
            if name.startswith(configuration.BACKUP_PREFIX): continue
            cur = cur.goto(name)
        return cur


    def get_file_view(self) -> Union[FileView, DirEntry]:
        if self.__file_view is None:
            self.__file_view = FileView(self.get_system_path())
        return self.__file_view


    def goto_path(self, fragment_path: list[str]) -> 'StorageEntry':
        entry: StorageEntry = self
        for name in fragment_path:
            entry = entry.goto(name)
        return entry


    def generate_url(self):
        if self.__cached_url is None:
            self.__cached_url = '/' + '/'.join(filter(quote, self.urlpath))
        return self.__cached_url


    def get_system_path(self) -> str:
        return configuration.STORAGE_PATH + os.sep + self.get_storage_path()


    def has_entries(self) -> bool:
        return self.get_file_view().is_dir()


    def scan_entries(self, include_backups=False, **kwargs) -> Iterator['StorageEntry']:
        if not self.read:
            raise PermissionError()
        if not self.has_entries():
            raise PermissionError()
        for entry in os.scandir(self.get_file_view().__fspath__()):
            if entry.is_symlink():
                if not ALLOW_LINKS:
                    continue
                try:
                    entry.stat(follow_symlinks=True)
                except FileNotFoundError:
                    continue
            if not include_backups and not SHOW_BACKUPS_IN_FILES and entry.name.startswith(BACKUP_PREFIX):
                continue
            yield self.goto(entry.name, fileview=entry, **kwargs)


    def __scan_backups(self, names_path: list[str]) -> Iterator['StorageEntry']:
        try:
            if is_filesystem_loop(self.get_system_path()):
                return
        except NotImplementedError:
            pass
        if len(names_path) == 0:
            yield self
        if not self.has_entries():
            return
        if len(names_path) > 0:
            for sub in self.goto(names_path[0]).__scan_backups(names_path[1:]):
                yield sub
        for entry in self.scan_entries(include_backups=True, promote_to_write=False):
            view = entry.get_file_view()
            try:
                if len(names_path) > 0:
                    if view.name == names_path[0]:
                        continue
                    if not os.path.exists(view.__fspath__() + os.sep + os.sep.join(names_path)):
                        continue
                elif self.is_real_file():
                    if view.is_dir() != self.get_file_view().is_dir():
                        continue
                    if view.is_file() != self.get_file_view().is_file():
                        continue
                if not view.name.startswith(configuration.BACKUP_PREFIX):
                    continue
                for sub in self.goto(entry.get_name()).__scan_backups(names_path):
                    yield sub
            except (PermissionError, FileNotFoundError):
                pass


    def scan_backups(self) -> Iterator['StorageEntry']:
        path = [self]
        while path[-1].read and path[-1].can_have_backup() and path[-1].parent is not None:
            path.append(path[-1].parent)
        if len(path) <= 1: return
        path.pop()
        search_root = path.pop()
        path.reverse()
        names = [e.get_name() for e in path]
        for backup in search_root.__scan_backups(names):
            if backup.generate_url() == self.generate_url(): continue
            yield backup


    def get_storage_path(self) -> str:
        if not self.read:
            raise PermissionError()
        raise NotImplementedError()


    def entry_exists(self, name: str) -> bool:
        try:
            self.goto(name)
            return True
        except FileNotFoundError:
            return False


    def create_dir_entry(self, name: str):
        os.mkdir(self.get_system_path() + os.sep + name)


    def make_backup(self, name: str, timestamp: Union[int, float, None] = None, move: bool = True):
        if not self.write: raise PermissionError()
        if timestamp is None: timestamp = time()
        source = self.goto(name).get_system_path()
        path = []
        backup_entry = self
        while backup_entry.has_name() and backup_entry.parent is not None and backup_entry.parent.write:
            path.append(backup_entry.get_name())
            backup_entry = backup_entry.parent
        path.append(configuration.BACKUP_PREFIX + datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d%H%M%S%f'))
        path.reverse()
        for subname in path:
            try:
                i = 1
                while True:
                    try_name = "%s_%i" % (subname, i) if i > 1 else subname
                    test_backup_entry = backup_entry.goto(try_name)
                    if test_backup_entry.has_entries():
                        backup_entry = test_backup_entry
                        break    
            except FileNotFoundError:
                backup_entry.create_dir_entry(subname)
                backup_entry = backup_entry.goto(subname)
        destination = backup_entry.get_system_path() + os.sep + name
        if move:
            shutil.move(source, destination)
        else:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copyfile(source, destination)


    def add_entry(self, name: str, source: str, timestamp: Union[int, float, None] = None, options: Literal['MOVE', 'LINK', 'NONE'] = 'MOVE'):
        if not self.write: raise PermissionError()
        if not self.has_entries(): raise PermissionError()
        if options == 'LINK' and not configuration.ALLOW_LINKS: raise PermissionError()
        try:
            self.make_backup(name, timestamp, move=True)
        except (FileNotFoundError, PermissionError) as err:
            pass
        destination = self.get_file_view().__fspath__()+os.sep+name
        if options == 'MOVE':
            shutil.move(source, destination)
        elif options == 'LINK':
            os.symlink(source, destination)
        else:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copyfile(source, destination)


    def remove_entry(self, name: str, timestamp: Union[int, float, None] = None):
        if not self.write: raise PermissionError()
        self.make_backup(name, timestamp, move=True)

    
    def rename_entry(self, old_name: str, new_name: str, timestamp: Union[int, float, None] = None):
        if not self.write: raise PermissionError()
        self.make_backup(old_name, timestamp, move=False)
        base_path = self.get_file_view().__fspath__()+os.sep
        shutil.move(base_path+old_name, base_path+new_name)


    def goto(self, name: str, **kwargs) -> 'StorageEntry':
        if not self.read: raise PermissionError()
        raise NotImplementedError()
