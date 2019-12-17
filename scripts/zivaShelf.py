import os
import maya.cmds as mc
import maya.mel as mel

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
    if 'image' in desc:
        mc.shelfButton(ctl, edit=True, image=desc['image'])

    # set the command
    if 'command' in desc:
        command_type = desc.get('commandType', 'python')
        mc.shelfButton(ctl, edit=True,
                       command=desc['command'], sourceType=command_type)


def _add_buttons(parent, desc):
    print 'Creating {0} shelf'.format(_SHELFNAME_)

    for ctl, but in desc['shelf']['buttons'].iteritems():
        mc.setParent(parent)

        width = but.get('width', 35)

        # create the control
        if but.get('separator', False):
            mc.separator(ctl, style='shelf', horizontal=False, width=width)
        else:
            # create button
            mc.shelfButton(ctl, parent=parent,
                           noDefaultPopup=True, flat=True, style='iconOnly',
                           h=35, w=width,
                           label=but['help'], ann=but['help'])
            _setup_button(but, ctl)


def build_shelf():
    """Build the Ziva shelf.
    """
    root = _shelf_root()
    shelves = mc.layout(root, q=True, ca=True)

    desc = _shelf_dict()

    if _SHELFNAME_ in shelves:
        mc.deleteUI(root + '|' + _SHELFNAME_, layout=True)
        shelves.remove(_SHELFNAME_)

    shelf = mel.eval('addNewShelfTab("{0}")'.format(_SHELFNAME_))
    lyt = mc.layout(shelf, q=True, ca=True)
    if lyt:
        for item in lyt:
            mc.deleteUI(item)
    _add_buttons(shelf, desc)
