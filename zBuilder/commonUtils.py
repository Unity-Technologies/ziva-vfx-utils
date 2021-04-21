import sys

'''
The module contains helper functions depends on Python features only.
'''

def none_to_empty(x):
    """
    Turn None into empty list, else just return the input as-is.

    This is a utility to work with Maya's Python API which returns
    None instead of empty list when no results are found.
    That non-uniformity is annoying. Use this to fix it.

    Args:
        x: anything
    Returns:
        [] if x is None else x
    """
    # Note, this could be x or [], but that would return empty
    # list for anything that evaluates to false, not just None.
    return [] if x is None else x


def is_string(var):
    # type: (str|unicode) -> bool
    '''
    Return True if input variable is string type, return False otherwise.

    TODO: Retire this function when type hints is introduced.
    '''
    if sys.version_info[0] < 3:
        return isinstance(var, basestring)
    return isinstance(var, str)
