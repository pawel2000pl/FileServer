PROHIBITED_CHARS = {'/', '\\', '~', ':', '<', '>', ':', '"', '|', '?', '*'}
for i in range(32): PROHIBITED_CHARS.add(chr(i))
for i in range(127, 192): PROHIBITED_CHARS.add(chr(i))
PROHIBITED_CHARS.add(chr(215))
PROHIBITED_CHARS.add(chr(247))
PROHIBITED_CHARS.remove(chr(142))
PROHIBITED_CHARS.remove(chr(138))


def check_filename(filename: str):
    if len(PROHIBITED_CHARS.intersection(filename)): return False
    if filename in {'..', '.', '~', '%'}: return False
    if filename.endswith('.') or filename.endswith(' ') or filename.startswith(' '): return False
    return True


def assert_filename(filename: str):
    if not check_filename(filename): raise PermissionError()


def check_path(path: list[str]):
    if not all(map(check_filename, path)): return False
    if len(path) < 1: return False
    if '..' in path or '.' in path: return False
    if any(map(lambda s: '/' in s or '\\' in s or s == '', path)): return False
    return True
