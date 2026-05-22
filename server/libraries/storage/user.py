import os
import models
import configuration
from os import DirEntry
from configuration import ALLOW_LINKS
from libraries.file_view import FileView
from libraries.storage import StorageEntry
from typing import Optional, Iterator, Union
from libraries.filename import assert_filename


class UserEntry(StorageEntry):

    def __init__(self, access_user: models.User, capability: Optional[models.Capability], pathuser: models.User, parent: StorageEntry, urlpath: list[str], storage_path: str, promote_to_write: bool = True, **kwargs):
        super().__init__(parent, urlpath, **kwargs)
        self.storage_path = storage_path
        view = self.get_file_view()
        view.stat(follow_symlinks=True)
        if not ALLOW_LINKS and view.is_symlink(): raise PermissionError()
        self.access_user = access_user
        self.capability = capability
        self.pathuser = pathuser
        self.read = parent.read or capability is not None and storage_path.startswith(capability.storage_path) and capability.user.id == access_user.id
        self.write = parent.write or (capability is not None and capability.write)
        if not self.read or (not self.write and promote_to_write):
            storage_path_parts = storage_path.split(os.sep)
            allowed_storage_paths = [os.sep.join(storage_path_parts[:i+1]) for i in range(len(storage_path_parts))]
            access_capability = models.Capability.query().where('user', access_user).where_in('storage_path', allowed_storage_paths).where('write').get_one()
            if access_capability is not None:
                self.read = True
                self.write = self.write or access_capability.write
                self.capability = access_capability


    def goto(self, name: str, **kwargs) -> 'StorageEntry':
        assert_filename(name)
        return UserEntry(self.access_user, self.capability, self.pathuser, self, self.urlpath+[name], self.storage_path+os.sep+name, **kwargs)


    def get_storage_path(self) -> str:
        return self.storage_path



class UserrootEntry(StorageEntry):

    def __init__(self, access_user: models.User, pathuser: models.User, parent: StorageEntry, urlpath: list[str]):
        super().__init__(parent, urlpath)
        self.access_user = access_user
        self.pathuser = pathuser
        self.read = access_user.id == pathuser.id
        self.write = False


    def goto(self, name: str, **kwargs) -> 'StorageEntry':
        path_capability = models.Capability.query().where('user', self.pathuser).where('name', name).get_one()
        if path_capability is None: raise FileNotFoundError()
        access_capability: Optional[models.Capability] = path_capability
        if self.access_user.id != self.pathuser.id:
            paths = path_capability.storage_path.split(os.sep)
            query = models.Capability.query()
            query.where('user', self.access_user)
            query.where_in('storage_path', [os.sep.join(paths[:i+1]) for i in range(len(paths))])
            query.order('write', 'DESC')
            access_capability = query.get_one()
        return UserEntry(self.access_user, access_capability, self.pathuser, self, self.urlpath+[name], path_capability.storage_path)


    def scan_entries(self, include_backups=False, **kwargs) -> Iterator[StorageEntry]:
        if self.access_user.id != self.pathuser.id:
            raise PermissionError()
        for cap in models.Capability().query().where('user', self.access_user).where_not_null('name').get():
            if not include_backups and not configuration.SHOW_BACKUPS_IN_FILES and cap.name.startswith(configuration.BACKUP_PREFIX):
                continue
            try:
                yield UserEntry(self.access_user, cap, self.pathuser, self, self.urlpath+[cap.name], cap.storage_path, **kwargs)
            except (PermissionError, FileNotFoundError):
                continue


    def has_entries(self) -> bool:
        return True


    def can_have_backup(self) -> bool:
        return True
