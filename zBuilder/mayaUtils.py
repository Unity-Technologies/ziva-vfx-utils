from maya import cmds

'''
The module contains helper functions depends on Maya Python API.
'''

def get_short_name(node_name):
    # type: (str) -> str
    '''
    Return short name of Maya node, if it's already short name, return it as is.
    '''
    return node_name.split('|')[-1]


def safe_rename(old_name, new_name):
    """
    Same as cmds.rename but does not throw an exception if renaming failed
    Useful if need to rename all the nodes that are not referenced
    """
    if old_name != new_name:
        try:
            return cmds.rename(old_name, new_name)
        except RuntimeError:
            pass

    return old_name


