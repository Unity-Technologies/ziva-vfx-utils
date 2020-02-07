import os
from maya import cmds


def get_icon_path_from_node(node):
    """Given a node, find the corresponding icon path that matches its type.

    Args:
        node (node): A node object to query.

    Returns:
        str: The path to the matching icon.
    """
    return get_icon_path_from_name(node.type)


def get_icon_path_from_name(name):
    """Given a name, find the corresponding icon path that matches.

    Args:
        name (str): A name of the icon to find.

    Returns:
        str: The path to the matching icon.
    """
    # look for repo icons first
    icons_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 '../..'))
    # if repo does not exist try to use Ziva module folder else ignore it
    if "icons" not in os.listdir(icons_folder):
        try:
            icons_folder = cmds.moduleInfo(moduleName='ZivaVFX', path=True)
        except RuntimeError:
            return ''

    return os.path.join(icons_folder, 'icons', '{name}.png'.format(name=name))
