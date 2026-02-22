import os
import models
import liteorm
from models import MainDatabaseModel
from typing import Optional, Union, Self, Literal, Collection


class Capability(MainDatabaseModel):

    id: int
    user: models.User
    token: str
    depends_on: 'Capability'
    name: str
    storage_path: str
    write: bool = False

    multi_index = [('user', 'storage_path')]
    unique_index = [('user', 'name'), 'token']
    not_null = ['storage_path']


    def before_persist(self):
        assert self.user is None or self.token is None
        assert self.storage_path is not None
        assert len(self.storage_path) > 0
        while self.storage_path.startswith(os.sep): self.storage_path[1:]
        while self.storage_path.endswith(os.sep): self.storage_path[:-1]
        if self.depends_on is not None:
            dependence = self.depends_on
            self.write = self.write and dependence.write
        if self.name is not None:
            if self.name == '': self.name = 'Unnamed'
            i = 2
            base_name = self.name
            while self.query().where('user', self.user).where('name', self.name).where_not('id', self.id).get_one() is not None:
                self.name = '%s (%d)'%(base_name, i)
                i += 1


    def after_persist(self):
        for cap in self.query().where('depends_on', self.id).get():
            if not cap.write or self.write: continue
            cap.persist(force=True)

