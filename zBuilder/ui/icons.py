from Qt import QtGui, QtWidgets, QtCore # https://github.com/mottosso/Qt.py by Marcus Ottosson
import os

def get_icon_path(node):
    name = ''
    if node.type == 'zAttachment':
        name = node.type
    else:
        name = node.type
    dirname = os.path.dirname(__file__)
    file_name = "{}\icons\{}.png".format(dirname, name)
    return file_name
