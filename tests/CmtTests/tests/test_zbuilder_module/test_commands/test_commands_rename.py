from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase
import zBuilder.commands as com
import unittest


class RenameTissueCommand(VfxTestCase):

    def setUp(self):
        cmds.polySphere(name='tissueMesh', ch=False)
        cmds.ziva(t=True)

        cmds.polySphere(name='restMesh', ch=False)
        cmds.select('tissueMesh', 'restMesh')
        cmds.zRestShape(a=True)

    def test_rename_single_tissue_reentry(self):
        for i in range(2):
            com.rename_ziva_nodes()
            self.assertTrue(cmds.objExists('tissueMesh_zTissue'))
            self.assertTrue(cmds.objExists('tissueMesh_zTet'))
            self.assertTrue(cmds.objExists('tissueMesh_zMaterial1'))
            self.assertTrue(cmds.objExists('tissueMesh_zRestShape'))


class RenameBoneCommand(VfxTestCase):

    def setUp(self):
        cmds.polySphere(name='boneMesh', ch=False)
        cmds.ziva(b=True)

    def test_rename_single_bone_reentry(self):
        for i in range(2):
            com.rename_ziva_nodes()
            self.assertTrue(cmds.objExists('boneMesh_zBone'))


class RenameClothCommand(VfxTestCase):

    def setUp(self):
        cmds.polySphere(name='clothMesh', ch=False)
        cmds.ziva(c=True)

    def test_rename_single_cloth_reentry(self):
        for i in range(2):
            com.rename_ziva_nodes()
            self.assertTrue(cmds.objExists('clothMesh_zCloth'))


class RenameAttachmentCommand(VfxTestCase):
    ''' This is a fix for VFXACT-1778 dealing with zAttachment suffix numbering.  In order to really see this
    you need to run rename_ziva_nodes multiple times in certain situations.  In these situations the numbers
    will get messed up and increment everytime you run rename_ziva_nodes.

    Note, I have seen this maya bug in our production assets and managed to reproduce it here.
    '''
    def setUp(self):
        cmds.polySphere(name='tissueMesh', ch=False)
        cmds.ziva(t=True)
        cmds.polySphere(name='boneMesh', ch=False)
        cmds.ziva(b=True)
        cmds.select('tissueMesh', 'boneMesh')
        cmds.ziva(a=True)
        cmds.select('tissueMesh', 'boneMesh')
        cmds.ziva(a=True)
        cmds.select('tissueMesh', 'boneMesh')
        cmds.ziva(a=True)

        # rename the numbers to confuse maya
        cmds.rename('zAttachment1', 'zAttachment4')
        cmds.rename('zAttachment2', 'zAttachment1')
        cmds.rename('zAttachment3', 'zAttachment5')
    def test_rename_single_attachment_reentry(self):
        # run this multiple times
        com.rename_ziva_nodes()
        com.rename_ziva_nodes()
        com.rename_ziva_nodes()
        com.rename_ziva_nodes()

        self.assertTrue(cmds.objExists('tissueMesh__boneMesh_zAttachment1'))
        self.assertTrue(cmds.objExists('tissueMesh__boneMesh_zAttachment2'))
        self.assertTrue(cmds.objExists('tissueMesh__boneMesh_zAttachment3'))

class RenameFiberCommand(VfxTestCase):

    def setUp(self):
        cmds.polySphere(name='tissueMesh', ch=False)
        cmds.ziva(t=True)
        cmds.select('tissueMesh')
        cmds.ziva(f=True)
        cmds.select('zFiber1')
        mel.eval('zLineOfActionUtil')
        cmds.rename('curve1', 'fiber_crv')
        cmds.select('fiber_crv', 'zFiber1')
        cmds.ziva(loa=True)

        cmds.polySphere(name='boneMesh', ch=False)
        cmds.ziva(b=True)

        cmds.select('fiber_crv.cv[0]', 'boneMesh')
        cmds.zRivetToBone()
        cmds.select('fiber_crv.cv[1]', 'boneMesh')
        print(cmds.zRivetToBone())

    @unittest.expectedFailure
    def test_rename_single_fiber_reentry(self):
        for i in range(2):
            com.rename_ziva_nodes()
            self.assertTrue(cmds.objExists('tissueMesh_zFiber1'))
            self.assertTrue(cmds.objExists('tissueMesh_zLineOfAction1'))
            self.assertTrue(cmds.objExists('fiber_crv_zRivet1'))
            self.assertTrue(cmds.objExists('fiber_crv_zRivetToBone1'))
            self.assertTrue(cmds.objExists('fiber_crv_zRivet2'))
