import os


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
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'icons', '{name}.png'.format(name=name))
