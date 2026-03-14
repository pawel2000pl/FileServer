
def assert_filename(filename: str):
    if len({'/', '\\', '~', ':'}.intersection(filename)): raise PermissionError()
    if filename in {'..', '.', '~'}: raise PermissionError()
