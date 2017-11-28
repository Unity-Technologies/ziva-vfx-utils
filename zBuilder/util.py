import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

import logging

logger = logging.getLogger(__name__)


def copy_paste(*args, **kwargs):
    '''
    A utility wrapper for copying and pasting a tissue
    '''
    sel = mc.ls(sl=True)

    selection = None
    if args:
        selection = mc.ls(args[0], l=True)
    else:
        selection = mc.ls(sl=True, l=True)

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_scene_selection(selection[0])
    z.string_replace(selection[0].split('|')[-1], selection[1].split('|')[-1])
    z.stats()
    z.build(**kwargs)

    mc.select(sel)


def check_map_validity():
    """
    This checks the map validity for zAttachments and zFibers.  For zAttachments
    it checks if all the values are zero.  If so it failed and turns off the
    associated zTissue node.  For zFibers it checks to make sure there are at least
    1 value of 0 and 1 value of .5 within a .1 threshold.  If not that fails and
    turns off the zTissue

    Returns:
        list of offending maps
    """
    sel = mc.ls(sl=True)
    import zBuilder.builders.ziva as zva

    # we are going to check fibers and attachments
    mc.select(mc.ls(type=['zAttachment', 'zFiber']), r=True)

    z = zva.Ziva()
    z.retrieve_from_scene_selection(connections=False)

    mz.check_map_validity(z.get_scene_items(type_filter='map'))

    mc.select(sel, r=True)


