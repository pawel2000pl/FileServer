import os
import models
from os import DirEntry
from typing import Optional
from configuration import ALLOW_LINKS
from libraries.file_view import FileView
from libraries.storage import StorageEntry


class TokenEntry(StorageEntry):

    def __init__(self, capability: models.Capability, parent: Optional[StorageEntry], urlpath: list[str], **kwargs):
        assert len(urlpath) >= 2
        super().__init__(parent, urlpath, **kwargs)
        self.capability = capability
        self.read = True
        self.write = capability.write
        view = self.get_file_view()
        view.stat(follow_symlinks=True)
        if not ALLOW_LINKS and view.is_symlink(): raise PermissionError()


    def get_name(self) -> str:
        if len(self.urlpath) == 2:
            return 'Unnamed share' if self.capability.name is None else self.capability.name
        return super().get_name()


    def goto(self, name: str, **kwargs) -> 'StorageEntry':
        if len({'/', '\\', '~', ':'}.intersection(name)): raise PermissionError()
        if name in {'..', '.', '~'}: raise PermissionError()
        return TokenEntry(self.capability, self, self.urlpath+[name], **kwargs)


    def get_storage_path(self) -> str:
        return os.sep.join([self.capability.storage_path] + self.urlpath[2:])


    def is_backup(self) -> bool:
        return False