import os
import cherrypy
import dataclasses
import configuration
from functools import wraps
from models import Capability, User
from libraries.file_view import FileView
from typing import Literal, Union, Collection, Self, Optional


@dataclasses.dataclass
class StorageEntry:
    url_path: list[str]
    storage_path: str
    system_path: str
    entry: FileView
    read: bool
    write: bool
    user: Optional[User] = None
    token: Optional[str] = None


    @classmethod
    def from_user(cls, user: Union[User, int], url_path: list[str]) -> Self:
        assert len(url_path) > 0
        if isinstance(user, int): user = User(id=user)
        base_cap = Capability.query().where('user', user).where('name', url_path[0]).get_one()
        if base_cap is None: raise PermissionError()
        read = True
        write = base_cap.write or Capability.query() \
                .where('user', user) \
                .where_in('storage_path', [os.sep.join([base_cap.storage_path]+url_path[1:i]) for i in range(1, len(url_path))]) \
                .where('write') \
                .get_one() is not None
        storage_path = os.sep.join([base_cap.storage_path]+url_path[1:])
        system_path = configuration.STORAGE_PATH + os.sep + storage_path
        entry = FileView(system_path)
        if not storage_path.startswith(base_cap.storage_path):
            raise PermissionError((base_cap.storage_path, storage_path))
        if not entry.__fspath__().startswith(FileView.absolute_filename(configuration.STORAGE_PATH)):
            raise PermissionError()
        return cls(url_path, storage_path, system_path, entry, read, write, user=user)


    @classmethod
    def from_token(cls, token: str, url_path: list[str]) -> Self:
        assert len(url_path) > 0
        base_cap = Capability.query().where('token', token).get_one()
        if base_cap is None: raise PermissionError()
        storage_path = os.sep.join([base_cap.storage_path]+url_path)
        system_path = configuration.STORAGE_PATH + os.sep + storage_path
        entry = FileView(system_path)
        read = False
        write = False
        query = Capability.query()
        query.where('token', token)
        query.where_in('storage_path', [os.sep.join([base_cap.storage_path]+url_path[:i]) for i in range(len(url_path))])
        for cap in query.get():
            read = read or cap.read
            write = write or cap.write
            if read and cap: break
        return cls(url_path, storage_path, system_path, entry, read, write, token=token)
        

    def shortest_storage_path(self, write_access: bool = False) -> str:
        if self.user is not None and self.user.is_admin: return ''
        query = Capability.query()
        if self.user is not None:
            query.where('user', self.user)
        elif self.token is not None:
            query.where('token', self.token)
        else:
            return self.storage_path
        if write_access: query.where('write')
        splitted = self.storage_path.split(os.sep)
        query.where_in('storage_path', [os.sep.join(splitted[:i]) for i in range(len(splitted))])
        query.order('storage_path', 'ASC')
        cap = query.get_one()
        if cap is not None:
            return cap.storage_path
        return self.storage_path
