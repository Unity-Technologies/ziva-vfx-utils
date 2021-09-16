from time import time
from functools import wraps
import logging
import sys
'''
The module contains helper functions depends on Python features only.
'''

logger = logging.getLogger(__name__)


def time_this(func):
    """
    A decorator to time functions.
    """
    @wraps(func)
    def new_function(*args, **kwargs):
        before = time()
        x = func(*args, **kwargs)
        after = time()
        logger.info("Executing {}() took {:.3f}s".format(func.__name__, (after - before)))
        return x

    return new_function


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


def is_sequence(var):
    """
    Returns:
    True if input is a sequence data type, i.e., list or tuple, but not string type.
    False otherwise.
    """
    return isinstance(var, (list, tuple)) and not is_string(var)


def get_first_element(maya_node):
    return maya_node[0] if is_sequence(maya_node) else maya_node
