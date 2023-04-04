from maya import cmds
from maya import mel
from zBuilder.utils.vfxUtils import cull_creation_nodes
from zBuilder.utils.mayaUtils import safe_rename
from .zivaBase import Ziva


class ClothNode(Ziva):
    """ This node for storing information related to zCloth.
    """
    type = 'zCloth'

    def do_build(self, *args, **kwargs):
        """ Builds the zCloth in maya scene.
        """

        scene_items = self.builder.get_scene_items(type_filter='zCloth')

        # checking if the node is the first one in list.  If it is I get
        # all the zCloth and build them together for speed reasons.
        # This feels kinda sloppy to me.

        if self is scene_items[0]:
            self.build_multiple()

            # set the attributes.  This needs to run even if there are no zCloth to build. This case happens during a copy paste.
            # any time you 'build' when the zCloth is in scene.
            for item in scene_items:
                item.set_maya_attrs()

    def build_multiple(self):
        """ Each node can deal with it's own building.  Though, with zCLoth it is much
        faster to build them all at once with one command instead of looping
        through them.  This function builds all the zCloth at once.
        """
        sel = cmds.ls(sl=True)
        scene_items = self.builder.get_scene_items(type_filter='zCloth')

        # cull none buildable------------------------------------------------------
        culled = cull_creation_nodes(scene_items)

        # build all cloth at once--------------------------------------------------
        results = None
        if culled['meshes']:
            Ziva.check_meshes(culled['meshes'])
            cmds.select(culled['meshes'], r=True)
            results = mel.eval('ziva -c')

        if results:
            # when creating a zCloth here we are using the ziva(c=True) command.  This
            # creates a zCloth and zMaterial.  We need to make sure that they
            # are named based on zBuilder data right after.  It is easier changing it here
            # when needed than to check and deal with it later.
            # rename zCloth
            for new_name, builder_name in zip(results[1::3], culled['names']):
                safe_rename(new_name, builder_name)

            # rename zMaterial
            for new_name, node in zip(results[2::3], culled['scene_items']):
                mesh = node.association
                for material in self.builder.get_scene_items(type_filter='zMaterial'):
                    if material.association == mesh:
                        safe_rename(new_name, material.name)
                        break

        cmds.select(sel)
