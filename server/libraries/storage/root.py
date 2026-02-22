from libraries.storage import StorageEntry
from libraries.storage import AccessModeEntry

class StorageRoot(StorageEntry):

    def __init__(self):
        super().__init__(None, [])


    def goto(self, name: str) -> StorageEntry:
        if name == 'userfile':
            return AccessModeEntry(self, 'userfile')
        if name == 'tokenfile':
            return AccessModeEntry(self, 'tokenfile')
        raise FileNotFoundError()
    

    def has_entries(self) -> bool:
        return False


    def is_backup(self) -> bool:
        return False

    
    def can_have_backup(self) -> bool:
        return False
    