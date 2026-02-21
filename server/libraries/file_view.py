import os
import sys
import stat
from typing import Any, cast, Optional


class FileView:

    def __init__(self, filename: str):
        self.path, self.name = self.absolute_path_and_basename(filename)
        self.__stat: dict[bool, Optional[os.stat_result]] = dict()


    @staticmethod
    def absolute_splitted_filename(filename: str, *, cwd: Optional[str] = None) -> list[str]:
        if cwd is None: cwd = os.getcwd()
        cwd += os.sep
        if cwd[0] == os.sep and filename.startswith(os.sep) or len(filename) >= 2 and filename[1] == ':': cwd = ''
        filename_parts = list(filter(lambda s: len(s) > 0 and s != '.', (cwd + filename).split(os.sep)))
        unified_parts = list[str]()
        for part in filename_parts:
            if part == '..': unified_parts.pop()
            else: unified_parts.append(part)
        return unified_parts


    @classmethod
    def absolute_path_and_basename(cls, filename: str) -> tuple[str, str]:
        cwd = os.getcwd()
        path_start = os.sep if cwd[0] == os.sep else ''
        unified_parts = cls.absolute_splitted_filename(filename, cwd=cwd)
        return path_start + os.sep.join(unified_parts[:-1]), unified_parts[-1]


    @classmethod
    def absolute_filename(cls, filename: str) -> str:
        path, name = cls.absolute_path_and_basename(filename)
        return path + os.sep + name


    def clear_cache(self):
        self.__stat = dict()


    def inode(self, *, follow_symlinks: bool = True) -> int:
        return self.stat(follow_symlinks=follow_symlinks).st_ino


    def is_dir(self, *, follow_symlinks: bool = True) -> bool:   
        try:     
            return stat.S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)
        except FileNotFoundError:
            return False


    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        try:
            return stat.S_ISREG(self.stat(follow_symlinks=follow_symlinks).st_mode)        
        except FileNotFoundError:
            return False


    def is_symlink(self) -> bool:
        try:
            return stat.S_ISLNK(self.stat(follow_symlinks=False).st_mode)        
        except FileNotFoundError:
            return False


    def exists(self, *, follow_symlinks: bool = True):
        try:
            self.stat(follow_symlinks=follow_symlinks)
            return True
        except FileNotFoundError:
            return False


    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        follow_symlinks = bool(follow_symlinks)
        try:
            if follow_symlinks not in self.__stat:
                self.__stat[follow_symlinks] = os.stat(self.__fspath__(), follow_symlinks=follow_symlinks)
        except FileNotFoundError:
            self.__stat[follow_symlinks] = None
        result = self.__stat[follow_symlinks]
        if result is None:
            raise FileNotFoundError(self.__fspath__())
        return result


    def __fspath__(self) -> str:
        return self.path + os.sep + self.name


    def __str__(self):
        return self.__repr__()


    def __repr__(self):
        return 'FileView('+repr(self.__fspath__())+')'