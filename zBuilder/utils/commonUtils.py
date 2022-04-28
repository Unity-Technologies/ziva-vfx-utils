import logging
import re
import sys

from functools import wraps
from time import time
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
    """ Return True if input variable is string type, return False otherwise.
    TODO: Retire this function when type hints is introduced.
    """
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


def clamp(val, min_val, max_val):
    """ Return value in [min_val, max_val] range.
    """
    # TODO: add type hint to check inputs are not None and are numeric types.
    assert val is not None
    assert min_val is not None
    assert max_val is not None
    assert isinstance(val, (int, float))
    assert isinstance(min_val, (int, float))
    assert isinstance(max_val, (int, float))
    assert min_val <= max_val

    return max(min(val, max_val), min_val)


def get_first_element(maya_node):
    return maya_node[0] if is_sequence(maya_node) else maya_node


def parse_version_info(version_string):
    """ Parse version info string to 4 element tuple.
    The first three are integer, the last one is string.
    The version info string format can be one of following form:
    1. major.minor.patch-tag
    2. major.minor.patch
    3. major.minor-tag
    4. major.minor
    """
    major = 0
    minor = 0
    patch = 0
    tag = ""
    match_result = re.search(r"^(\d+)\.(\d+)?(\.(\d+))?(-(.*))?$", version_string)
    assert match_result, "Invalid zBuilder version info format, should be major.minor[.patch][-tag] form."

    try:
        major = int(match_result.group(1))
        assert major >= 0, "Major number ({}) must be integer.".format(major)

        assert match_result.group(2), "Minor number must be integer."
        minor = int(match_result.group(2))
        assert minor >= 0, "Minor number ({}) must be integer.".format(minor)

        if match_result.group(4):
            patch = int(match_result.group(4))
        assert patch >= 0, "Patch number ({}) must be integer.".format(patch)

        if match_result.group(6):
            tag = match_result.group(6)
    except ValueError:
        logger.error("Major/minor/patch strings can't cast to integer.")

    return major, minor, patch, tag