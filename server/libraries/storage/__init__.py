from libraries.storage.entry import StorageEntry
from libraries.storage.user import UserEntry, UserrootEntry
from libraries.storage.token import TokenEntry
from libraries.storage.access_mode import AccessModeEntry
from libraries.storage.root import StorageRoot


def UrlStorage(url: list[str]) -> StorageEntry:
    return StorageRoot().goto_path(url)
