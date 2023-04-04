from maya import cmds
from maya import mel
from zBuilder.utils.mayaUtils import safe_rename
from zBuilder.utils.vfxUtils import cull_creation_nodes
from .zivaBase import Ziva


class BoneNode(Ziva):
    """ This node for storing information related to zBones.
    """
    type = 'zBone'

    def do_build(self, *args, **kwargs):
        """ Builds the zBones in maya scene.
        """

        scene_items = self.builder.get_scene_items(type_filter='zBone')

        # checking if the node is the first one in list.  If it is I get
        # all the zBones and build them together for speed reasons.
        # This feels kinda sloppy to me.
        if self is scene_items[0]:
            build_multiple(scene_items)

            # Set the attributes.
            # This needs to run even if there are no zBone to build.
            # This case happens during a copy paste.
            # any time you 'build' when the zBone is in scene.
            for scene_item in scene_items:
                scene_item.set_maya_attrs()


def build_multiple(scene_items):
    """ Builds all the zBones at once.
    Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.
    """
    sel = cmds.ls(sl=True)
    # cull none buildable------------------------------------------------------
    culled = cull_creation_nodes(scene_items)

    # build bones all at once--------------------------------------------------
    results = None
    if culled['meshes']:
        Ziva.check_meshes(culled['meshes'])
        cmds.select(culled['meshes'], r=True)
        results = mel.eval('ziva -b')

    # rename zBones------------------------------------------------------------
    if results:
        results = cmds.ls(results, type='zBone')
        for new, name, scene_item in zip(results, culled['names'], culled['scene_items']):
            scene_item.name = safe_rename(new, name)

    cmds.select(sel)
