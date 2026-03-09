import flask
import models
import libraries.storage
from libraries.storage import StorageEntry
from typing import Literal

class AccessModeEntry(StorageEntry):

    def __init__(self, root: StorageEntry, storage_type: Literal['userfile', 'tokenfile']):
        super().__init__(root, [storage_type])
        self.type = storage_type


    def goto(self, name: str, **kwargs) -> 'StorageEntry':
        if self.type == 'tokenfile':
            return self.__goto_token(name)
        if self.type == 'userfile':
            return self.__goto_user(name)
        assert False


    def __goto_token(self, token: str) -> 'StorageEntry':
        cap = models.Capability.query().where('token', token).get_one()
        if cap is None: raise FileNotFoundError()
        return libraries.storage.TokenEntry(cap, self, self.urlpath+[token])


    def __goto_user(self, username: str) -> 'StorageEntry':
        logged_user_id = flask.session.get('user_id')
        if logged_user_id is None: raise PermissionError()
        logged_user = models.User(id=logged_user_id)
        user = models.User.query().where('name', username).get_one()
        if user is None: raise FileNotFoundError()
        return libraries.storage.UserrootEntry(logged_user, user, self, self.urlpath+[username])


    def has_entries(self) -> bool:
        return False


    def is_backup(self) -> bool:
        return False