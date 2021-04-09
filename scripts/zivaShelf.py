import os
from maya import cmds
from maya import mel

import json
from collections import OrderedDict

_SHELFNAME_ = "Ziva"
_JSONFILE_ = "shelf.json"


def _shelf_root():
    return mel.eval('global string $gShelfTopLevel;$tmp = $gShelfTopLevel;')


def _shelf_dict():
    """Read the shelf

    Returns:
    - The shelf dictionary

    Raises:
    - Exception: If the standard shelf can not be loaded.
    """

    fpath = os.path.join(os.path.dirname(__file__), _JSONFILE_)
    try:
        with open(fpath) as fh:
            shelf_dict = json.load(fh, object_pairs_hook=OrderedDict)
    except:
        raise Exception('Could not read standard shelf "{0}"'.format(fpath))

    return shelf_dict


def _setup_button(desc, ctl):
    # set the icon
    icon_name = desc['image']
    cmds.shelfButton(ctl, edit=True, image=icon_name)

    # set the command
    command_type = desc.get('commandType', 'python')
    cmds.shelfButton(ctl, edit=True, command=desc['command'], sourceType=command_type)


def _add_buttons(parent, desc):
    for ctl, but in desc['shelf']['buttons'].items():
        cmds.setParent(parent)

        width = but.get('width', 35)

        # create the control
        if but.get('separator', False):
            cmds.separator(ctl, style='shelf', horizontal=False, width=width)
        else:
            # create button
            cmds.shelfButton(ctl,
                             parent=parent,
                             noDefaultPopup=True,
                             flat=True,
                             style='iconOnly',
                             h=35,
                             w=width,
                             label=but['help'],
                             ann=but['help'])
            _setup_button(but, ctl)


def build_shelf():
    """Build the Ziva shelf.
    """
    root = _shelf_root()
    shelves = cmds.layout(root, q=True, ca=True)

    desc = _shelf_dict()

    if _SHELFNAME_ in shelves:
        cmds.deleteUI(root + '|' + _SHELFNAME_, layout=True)
        shelves.remove(_SHELFNAME_)

    shelf = mel.eval('addNewShelfTab("{0}")'.format(_SHELFNAME_))
    lyt = cmds.layout(shelf, q=True, ca=True)
    if lyt:
        for item in lyt:
            cmds.deleteUI(item)
    _add_buttons(shelf, desc)
