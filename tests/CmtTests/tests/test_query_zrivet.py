from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase


class QueryRivetTestCase(VfxTestCase):
    '''
    This is the test case for zRivetToBone query.
    Currently it verifies zQuery MEL script, 
    it will verify Python script once zQuery migrates.
    '''
    def setUp(self):
        super(QueryRivetTestCase, self).setUp()

    def tearDown(self):
        super(QueryRivetTestCase, self).tearDown()

    def create_bone(self, name, position):
        '''
        Create a cube zBone with specified name and position
        Args:
            name(string): Cube mesh name
            position(list): Cube mesh position coordinates
        Returns:
            (tuple): (Cube mesh name, zBone name)
        '''
        cube_mesh = cmds.polyCube(n=name)
        cmds.move(position[0], position[1], position[2])
        zBone = mel.eval('ziva -b {}'.format(cube_mesh[0]))
        return (cube_mesh[0], zBone[-1])

    def create_line(self, point1, point2, name):
        '''
        Create a NURBS line with specified points and name
        Args:
            point1, point2(list): End point coordinates
            name(string): new curve name
        Returns:
            Created line name, may different from the input if it exists in the scene.
        '''
        pt1_string = ' '.join(str(i) for i in point1)
        pt2_string = ' '.join(str(i) for i in point2)
        line = mel.eval('curve -d 1 -p {} -p {} -k 0 -k 1 -n {}'.format(
            pt1_string, pt2_string, name))
        return line

    def create_rivet(self, cv, bone):
        '''
        Create a zRivetToBone with input control vertex(CV) and zBone
        Args:
            cv(string): Control vertex of the line
            bone(string): zBone
        Returns:
            (list): [zRiveToBone, zRivetToBoneLocator]
        '''
        return mel.eval('zRivetToBone {} {}'.format(cv, bone))

    def test_empty_scene_and_solver(self):
        # Empty scene
        query_result = mel.eval('zQuery -rtb')
        self.assertIsNone(query_result)

        # One empty solver
        mel.eval('ziva -s')
        query_result = mel.eval('zQuery -rtb')
        self.assertIsNone(query_result)

    def test_one_solver_one_bone(self):
        # Setup
        bone1 = self.create_bone('bone1', (-1, 0, 0))
        line1 = self.create_line((-1, 0, 0), (1, 0, 0), 'line1')
        rivet1 = self.create_rivet('{}.cv[{}]'.format(line1, 0), bone1[1])
        rivet2 = self.create_rivet('{}.cv[{}]'.format(line1, 1), bone1[1])

        # Action
        # Clear the selection to collect all rivets.
        cmds.select(clear=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0]])

        # Action
        # Select the bone
        cmds.select('bone1', r=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0]])

        # Action
        # Select the curve
        cmds.select('line1', r=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        # Query does not take account the curve selection
        self.assertIsNone(query_result)

    def test_rivets_with_two_bones(self):
        '''
        Verify queries on curve rivets on different bones.
        Two curves's end points rivet to two bones respectively.
        '''
        # Setup
        bone1 = self.create_bone('bone1', (-1, 0, 0))
        bone2 = self.create_bone('bone2', (1, 0, 0))
        line1 = self.create_line((-1, 0, -1), (1, 0, -1), 'line1')
        rivet1 = self.create_rivet('{}.cv[{}]'.format(line1, 0), bone1[1])
        rivet2 = self.create_rivet('{}.cv[{}]'.format(line1, 1), bone2[1])
        line2 = self.create_line((-1, 0, 1), (1, 0, 1), 'line2')
        rivet3 = self.create_rivet('{}.cv[{}]'.format(line2, 0), bone1[1])
        rivet4 = self.create_rivet('{}.cv[{}]'.format(line2, 1), bone2[1])

        # Action
        # Clear the selection to collect all rivets.
        cmds.select(clear=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0], rivet3[0], rivet4[0]])

        # Action
        # Select one bone
        cmds.select('bone1', r=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet3[0]])

        # Select the other bone
        cmds.select('bone2', r=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet2[0], rivet4[0]])

        # Follow previous selection, select both bones
        cmds.select('bone1', add=True)
        query_result = mel.eval('zQuery -rivetToBone')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0], rivet3[0], rivet4[0]])

    def test_two_solvers(self):
        '''
        Verify queries on rivets across multiple solvers.
        Two curves's end points rivet to two bones respectively.
        '''
        # Setup
        # Bone1 in Solver1, Bone2 in Solver2
        solver1 = mel.eval('ziva -s')
        cmds.select(solver1[1], r=True)
        cmds.ziva(defaultSolver=True)
        bone1 = self.create_bone('bone1', (-1, 0, 0))
        solver2 = mel.eval('ziva -s')
        cmds.select(solver2[1], r=True)
        cmds.ziva(defaultSolver=True)
        bone2 = self.create_bone('bone2', (1, 0, 0))
        # Lines' endpoints rivets to bones respectively
        line1 = self.create_line((-1, 0, -1), (1, 0, -1), 'line1')
        rivet1 = self.create_rivet('{}.cv[{}]'.format(line1, 0), bone1[1])
        rivet2 = self.create_rivet('{}.cv[{}]'.format(line1, 1), bone2[1])
        line2 = self.create_line((-1, 0, 1), (1, 0, 1), 'line2')
        rivet3 = self.create_rivet('{}.cv[{}]'.format(line2, 0), bone1[1])
        rivet4 = self.create_rivet('{}.cv[{}]'.format(line2, 1), bone2[1])

        # Action
        # Clear the selection to collect all rivets.
        cmds.select(clear=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0], rivet3[0], rivet4[0]])

        # Action
        # Select one bone
        cmds.select('bone1', r=True)
        query_result = mel.eval('zQuery -rivetToBone')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet3[0]])

        # Select the other bone
        cmds.select('bone2', r=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet2[0], rivet4[0]])

        # Follow previous selection, select both bones
        cmds.select('bone1', add=True)
        query_result = mel.eval('zQuery -rtb')

        # Verify
        self.assertEqual(sorted(query_result), [rivet1[0], rivet2[0], rivet3[0], rivet4[0]])
