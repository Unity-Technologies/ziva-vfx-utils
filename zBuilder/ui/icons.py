import os

def get_icon_path_from_node(node):
    name = ''
    if node.type == 'zAttachment':
        name = node.type
    else:
        name = node.type
    dirname = os.path.dirname(__file__)
    file_name = "{}\icons\{}.png".format(dirname, name)
    return file_name

def get_icon_path_from_name(name):
    dirname = os.path.dirname(__file__)
    file_name = "{}\icons\{}.png".format(dirname, name)
    return file_name
