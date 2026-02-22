import os
import models
from typing import Optional
from libraries.storage import StorageEntry


class TokenEntry(StorageEntry):
    
    def __init__(self, capability: models.Capability, parent: Optional[StorageEntry], urlpath: list[str]):
        assert len(urlpath) >= 2
        super().__init__(parent, urlpath)
        self.capability = capability
        self.read = True
        self.write = capability.write
        if not self.get_file_view().exists(): raise FileNotFoundError()


    def goto(self, name: str) -> 'StorageEntry':
        if len({'/', '\\', '~', ':'}.intersection(name)): raise PermissionError()
        if name in {'..', '.', '~'}: raise PermissionError()
        return TokenEntry(self.capability, self, self.urlpath+[name])


    def get_storage_path(self) -> str:
        return self.capability.storage_path + os.sep + os.sep.join(self.urlpath[2:])


    def is_backup(self) -> bool:
        return False