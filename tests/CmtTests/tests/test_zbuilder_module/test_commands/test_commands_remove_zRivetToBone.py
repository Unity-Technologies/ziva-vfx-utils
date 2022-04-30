from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.commands import remove_zRivetToBone_nodes


def create_bone(name, solver=None):
    cmds.polyCube(n=name)
    if solver:
        cmds.ziva(solver, name, b=True)
    else:
        cmds.ziva(name, b=True)


def create_tissue_with_fiber(name):
    cmds.polySphere(n=name)
    cmds.ziva(name, t=True)
    cmds.ziva(name, f=True)


def create_curve(name):
    cmds.curve(d=1, p=[(1, 0, 0), (5, 0, 0)], k=[0, 1], n=name)


def bind_rivet_to_bone(cv, bone):
    return cmds.zRivetToBone(cv, bone)


def get_rivet_name_triplet(index):
    return ('zRivet{}'.format(index), 'zRivet{}Shape'.format(index), 'zRivetToBone{}'.format(index))


class RemoveRivetToBoneTestCase(VfxTestCase):
    '''
    Test delete_zRivetToBone command
    '''

    def bone_rivet_setup(self):
        create_bone('bone1')
        create_curve('curve1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')

    def bone_two_rivets_setup(self):
        create_bone('bone1')
        create_curve('curve1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        bind_rivet_to_bone('curve1.cv[1]', 'bone1')
        create_curve('curve2')
        bind_rivet_to_bone('curve2.cv[0]', 'bone1')
        bind_rivet_to_bone('curve2.cv[1]', 'bone1')

    def bone_share_curve_setup(self):
        create_bone('bone1')
        create_bone('bone2')
        create_curve('curve1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone2')

    def two_bones_with_respective_rivets_setup(self):
        create_bone('bone1')
        create_curve('curve1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        create_bone('bone2')
        create_curve('curve2')
        bind_rivet_to_bone('curve2.cv[0]', 'bone2')
        bind_rivet_to_bone('curve2.cv[0]', 'bone2')

    def two_solver_with_respective_bones_rivets_setup(self):
        cmds.ziva(s=True)
        cmds.ziva(s=True)
        create_bone('bone1', solver='zSolver1')
        create_curve('curve1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        bind_rivet_to_bone('curve1.cv[0]', 'bone1')
        create_bone('bone2', solver='zSolver2')
        create_curve('curve2')
        bind_rivet_to_bone('curve2.cv[0]', 'bone2')
        bind_rivet_to_bone('curve2.cv[0]', 'bone2')

    def delete_selected_node_rivet(self, setup_op, nodes):
        '''
        Helper function that loads specified scene, deletes specified nodes, 
        and returns actual deleted nodes.
        '''
        # Setup
        setup_op()
        nodes_before = set(cmds.ls())

        # Action
        cmds.select(clear=True)
        cmds.select(nodes)
        remove_zRivetToBone_nodes(nodes)
        nodes_after = set(cmds.ls())
        deleted_nodes = nodes_before - nodes_after
        return deleted_nodes

    # -------------------------------------------------------------------------
    # Test cases
    # -------------------------------------------------------------------------
    def test_delete_none_with_nothing_selected(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, [])

        # Verify
        self.assertEqual(len(deleted_nodes), 0)

    def test_delete_rivet_with_selected_mesh(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, ['bone1'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_rivet_with_selected_bone(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, ['zBone1'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_rivet_with_selected_rivet(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, ['zRivetToBone1'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_rivet_with_selected_rivet_locator_transform(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, ['zRivet1'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_rivet_with_selected_rivet_locator(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_rivet_setup, ['zRivet1Shape'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_selected_zbone_all_rivets(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_two_rivets_setup, ['zBone1'])

        # Verify
        expected_deleted_nodes = set(
            get_rivet_name_triplet(1) + get_rivet_name_triplet(2) + get_rivet_name_triplet(3) +
            get_rivet_name_triplet(4))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))

    def test_delete_rivet_with_share_curve_rivets(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.bone_share_curve_setup, ['zRivet1'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))
        expected_remained_nodes = set(get_rivet_name_triplet(2))
        self.assertTrue(expected_remained_nodes.isdisjoint(deleted_nodes))

    def test_delete_rivet_with_different_bones(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(self.two_bones_with_respective_rivets_setup,
                                                        ['zRivet1', 'zRivet3'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1) + get_rivet_name_triplet(3))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))
        expected_remained_nodes = set(get_rivet_name_triplet(2) + get_rivet_name_triplet(4))
        self.assertTrue(expected_remained_nodes.isdisjoint(deleted_nodes))

    def test_delete_rivet_through_rivet_with_different_bones_on_different_solver(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(
            self.two_solver_with_respective_bones_rivets_setup, ['zRivet1', 'zRivet3'])

        # Verify
        expected_deleted_nodes = set(get_rivet_name_triplet(1) + get_rivet_name_triplet(3))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))
        expected_remained_nodes = set(get_rivet_name_triplet(2) + get_rivet_name_triplet(4))
        self.assertTrue(expected_remained_nodes.isdisjoint(deleted_nodes))

    def test_delete_rivet_through_zbone_with_different_bones_on_different_solver(self):
        # Setup & Action
        deleted_nodes = self.delete_selected_node_rivet(
            self.two_solver_with_respective_bones_rivets_setup, ['zBone1', 'zBone2'])

        # Verify
        expected_deleted_nodes = set(
            get_rivet_name_triplet(1) + get_rivet_name_triplet(2) + get_rivet_name_triplet(3) +
            get_rivet_name_triplet(4))
        self.assertTrue(expected_deleted_nodes.issubset(deleted_nodes))
