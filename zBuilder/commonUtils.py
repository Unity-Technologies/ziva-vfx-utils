import sys

def is_string(var):
    # type: (str|unicode) -> bool
    '''
    Return True if input variable is string type, return False otherwise.

    TODO: Retire this function when type hints is introduced.
    '''
    if sys.version_info[0] < 3:
        return isinstance(var, basestring)
    return isinstance(var, str)
