import os
import models
from typing import Optional
from configuration import ALLOW_LINKS
from libraries.storage import StorageEntry


class TokenEntry(StorageEntry):

    def __init__(self, capability: models.Capability, parent: Optional[StorageEntry], urlpath: list[str]):
        assert len(urlpath) >= 2
        super().__init__(parent, urlpath)
        self.capability = capability
        self.read = True
        self.write = capability.write
        if not self.get_file_view().exists(): raise FileNotFoundError()
        if not ALLOW_LINKS and self.get_file_view().is_symlink(): raise PermissionError()


    def get_name(self) -> str:
        if len(self.urlpath) == 2:
            return 'Unnamed share' if self.capability.name is None else self.capability.name
        return super().get_name()


    def goto(self, name: str) -> 'StorageEntry':
        if len({'/', '\\', '~', ':'}.intersection(name)): raise PermissionError()
        if name in {'..', '.', '~'}: raise PermissionError()
        return TokenEntry(self.capability, self, self.urlpath+[name])


    def get_storage_path(self) -> str:
        return os.sep.join([self.capability.storage_path] + self.urlpath[2:])


    def is_backup(self) -> bool:
        return False