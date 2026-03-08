import os

MAX_DEPTH = 256
FIRST_CHECK = round(MAX_DEPTH**0.25)

def is_filesystem_loop(path: str) -> bool:
    for i in range(len(path)):
        if path[i] != os.sep:
            continue
        if os.path.exists(path[:i] + path[i:] * FIRST_CHECK):
            return True
        elif os.path.exists(path[:i] + path[i:] * MAX_DEPTH):
            return True
    return False
