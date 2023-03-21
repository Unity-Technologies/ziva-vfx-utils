import os

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase, attr_values_from_scene
from zBuilder.builders.deformers import Deformers


class DeformerBuilderTestCase(VfxTestCase):

    def setUp(self):
        super(DeformerBuilderTestCase, self).setUp()
        cmds.polySphere(n='skin')
        cmds.polySphere(n='wrapTarget1')
        cmds.polySphere(n='wrapTarget2')
        cmds.polySphere(n='blendShapeTarget1')
        cmds.polySphere(n='blendShapeTarget2')
        cmds.select(cl=True)
        cmds.joint(n='influence')

        cmds.select('skin', 'wrapTarget1')
        mel.eval('doWrapArgList "7" { "1","0","1", "2", "0", "1", "0", "0" }')
        cmds.select('skin', 'influence')
        cmds.skinCluster()
        cmds.select('skin')
        cmds.deltaMush()
        cmds.select('skin')
        cmds.deltaMush()
        cmds.select('blendShapeTarget1', 'skin')
        cmds.blendShape()
        cmds.select('blendShapeTarget1', 'skin')
        cmds.blendShape()
        cmds.select('skin', 'wrapTarget2')
        mel.eval('doWrapArgList "7" { "1","0","1", "2", "0", "1", "0", "0" }')
        cmds.select('skin')
        cmds.deltaMush()

    def test_deformers_order(self):
        ## SETUP
        acquire = ['deltaMush', 'blendShape', 'wrap', 'skinCluster']
        pre_history = cmds.listHistory('skin', )
        pre_nodes = [x for x in pre_history if cmds.objectType(x) in acquire]

        ## ACT
        cmds.select('skin')
        builder = Deformers()
        builder.retrieve_from_scene()

        cmds.select(cmds.ls(type='mesh'))
        cmds.delete(ch=True)  # delete construction history on meshes to start over

        builder.build()

        ## VERIFY
        post_history = cmds.listHistory('skin', )
        post_nodes = [x for x in post_history if cmds.objectType(x) in acquire]

        self.assertEqual(pre_nodes, post_nodes)


    def test_supported_nodes_filter(self):
        # checking the internal deformers attribute is reflecting changes to deformers.
        ## SETUP + ACT
        cmds.select('skin')
        builder = Deformers()
        builder.retrieve_from_scene(deformers=['wrap'])

        # VERIFY
        self.assertEqual(builder.deformers, ['wrap'])

        ## SETUP + ACT
        cmds.select('skin')
        builder = Deformers()
        builder.retrieve_from_scene(deformers=['deltaMush', 'garbage'])

        # VERIFY
        self.assertEqual(builder.deformers, ['deltaMush'])

        ## SETUP + ACT
        cmds.select('skin')
        builder = Deformers()
        builder.retrieve_from_scene(deformers=[111111])

        # VERIFY
        self.assertEqual(builder.deformers, [])