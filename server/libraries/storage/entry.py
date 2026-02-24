import os
import configuration
from os import DirEntry
from urllib.parse import quote
from configuration import ALLOW_LINKS
from libraries.file_view import FileView
from typing import Optional, Iterator, Union

class StorageEntry:

    def __init__(self, parent: Optional['StorageEntry'], urlpath: list[str]):
        self.parent = parent
        self.urlpath = urlpath
        self.read = False
        self.write = False
        self.__file_view: Optional[FileView] = None
        self.__cached_url: Optional[str] = None


    def get_name(self) -> str:
        if len(self.urlpath) == 0:
            raise PermissionError()
        return self.urlpath[-1]


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


    def get_file_view(self) -> FileView:
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


    def get_file_entry(self) -> FileView:
        if not self.read:
            raise PermissionError()
        return FileView(self.get_system_path())


    def has_entries(self) -> bool:
        return self.get_file_entry().is_dir()


    def scan_entries(self) -> Iterator[Union[FileView, DirEntry]]:
        if not self.read:
            raise PermissionError()
        if not self.has_entries():
            raise PermissionError()
        for entry in os.scandir(self.get_file_entry().__fspath__()):
            if ALLOW_LINKS or not entry.is_symlink():
                yield entry


    def __scan_backups(self, names_path: list[str], shared_set: set) -> Iterator['StorageEntry']:
        try:
            my_path = os.path.realpath(self.get_system_path())
            if my_path in shared_set or len(shared_set) > configuration.BACKUPS_SCAN_LIMIT:
                return
            shared_set.add(my_path)
        except NotImplementedError:
            pass
        if len(names_path) == 0:
            yield self
        if not self.has_entries():
            return
        if len(names_path) > 0:
            for sub in self.goto(names_path[0]).__scan_backups(names_path[1:], shared_set):
                yield sub
        for entry in self.scan_entries():
            try:
                if len(names_path) > 0:
                    if entry.name == names_path[0]:
                        continue
                    if not os.path.exists(entry.__fspath__() + os.sep + os.sep.join(names_path)):
                        continue
                elif self.is_real_file():
                    if entry.is_dir() != self.get_file_view().is_dir():
                        continue
                    if entry.is_file() != self.get_file_view().is_file():
                        continue
                if not entry.name.startswith(configuration.BACKUP_PREFIX):
                    continue
                for sub in self.goto(entry.name).__scan_backups(names_path, shared_set):
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
        for backup in search_root.__scan_backups(names, set()):
            if backup.generate_url() == self.generate_url(): continue
            yield backup
        

    def get_storage_path(self) -> str:
        if not self.read:
            raise PermissionError()
        raise NotImplementedError()


    def goto(self, name: str) -> 'StorageEntry':
        if not self.read:
            raise PermissionError()
        raise NotImplementedError()