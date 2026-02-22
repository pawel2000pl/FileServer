import os
import models
import configuration
from os import DirEntry
from libraries.file_view import FileView
from libraries.storage import StorageEntry
from typing import Optional, Iterator, Union


class UserEntry(StorageEntry):
    
    def __init__(self, access_user: models.User, capability: Optional[models.Capability], pathuser: models.User, parent: StorageEntry, urlpath: list[str], storage_path: str):
        super().__init__(parent, urlpath)
        self.storage_path = storage_path
        self.access_user = access_user
        self.capability = capability
        self.pathuser = pathuser
        self.read = parent.read or capability is not None
        self.write = parent.write or (capability is not None and capability.write)
        if not self.read or not self.write:
            access_capability = models.Capability.query().where('user', access_user).where('storage_path', storage_path).order('write', 'DESC').get_one()
            if access_capability is not None:
                self.read = True
                self.write = self.write or access_capability.write
                self.capability = access_capability
                self.urlpath = ['userfile', access_user.name, access_capability.name]
        if not self.get_file_view().exists(): raise FileNotFoundError()


    def goto(self, name: str) -> 'StorageEntry':
        if len({'/', '\\', '~', ':'}.intersection(name)): raise PermissionError()
        if name in {'..', '.', '~'}: raise PermissionError()
        return UserEntry(self.access_user, self.capability, self.pathuser, self, self.urlpath+[name], self.storage_path+os.sep+name)


    def get_storage_path(self) -> str:
        return self.storage_path



class UserhomeEntry(StorageEntry):

    def __init__(self, access_user: models.User, pathuser: models.User, parent: StorageEntry, urlpath: list[str]):
        super().__init__(parent, urlpath)
        self.access_user = access_user
        self.pathuser = pathuser
        self.read = access_user.id == pathuser.id
        self.write = False


    def goto(self, name: str) -> 'StorageEntry':
        path_capability = models.Capability.query().where('user', self.pathuser).where('name', name).get_one()
        if path_capability is None: raise FileNotFoundError()
        access_capability = path_capability if self.access_user.id == self.pathuser.id else models.Capability.query().where('user', self.access_user).where('name', name).order('write', 'DESC').get_one() 
        return UserEntry(self.access_user, access_capability, self.pathuser, self, self.urlpath+[name], path_capability.storage_path)


    def scan_entries(self) -> Iterator[Union[FileView, DirEntry]]:
        if self.access_user.id != self.pathuser.id:
            raise PermissionError()
        for cap in models.Capability().query().where('user', self.access_user).where_not_null('name').get():
            yield FileView(configuration.STORAGE_PATH + os.sep + cap.storage_path)


    def get_file_entry(self) -> FileView:
        raise PermissionError()
        

    def has_entries(self) -> bool:
        return True

    
    def can_have_backup(self) -> bool:
        return True