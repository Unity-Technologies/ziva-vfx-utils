import logging

from maya import cmds
from maya.api import OpenMaya as om2
from zBuilder.utils.mayaUtils import get_dag_path_from_mesh, get_name_from_mobject, get_maya_api_version
from ..base import Base

logger = logging.getLogger(__name__)


class Mesh(Base):
    type = 'mesh'

    def __init__(self, *args, **kwargs):
        super(Mesh, self).__init__(*args, **kwargs)

        self._pCountList = []
        self._pConnectList = []
        self._pointList = []

        if args:
            mesh_name = args[0]
            if mesh_name:
                self.populate(mesh_name)

    def __str__(self):
        if self._pCountList and self._pointList:
            return "< MESH: {} -- Poly: {}  Vert: {} >".format(self.long_name,
                                                               len(self._pCountList),
                                                               len(self._pointList))
        else:
            return "< MESH: {} -- Not retrieved yet. >".format(self.long_name)

    def __repr__(self):
        return self.__str__()

    def populate(self, mesh_name):
        """ Populate node with that from the maya scene.

         Args:
             mesh_name: Name of mesh to populate it with.
        """
        self.name = mesh_name
        self.type = 'mesh'
        # Defer retrieve mesh value to retrieve_values() until it is needed.

    def retrieve_values(self):
        # get the values of the mesh from the scene and update the scene_item
        self._pCountList, self._pConnectList, self._pointList = get_mesh_info(self.long_name)

    def build_mesh(self):
        """ Builds mesh in maya scene.

        Returns:
            Name of newly built mesh.
        """
        # Thanks to Maya Python API 2.0, we can copy python list to M*Array in the constructor
        mesh_fn = om2.MFnMesh()
        new_mesh = mesh_fn.create(om2.MPointArray(self._pointList), om2.MIntArray(self._pCountList),
                                  om2.MIntArray(self._pConnectList))
        new_mesh_dep_node = om2.MFnDependencyNode(new_mesh)
        return cmds.rename(new_mesh_dep_node.name(), self.name + '_rebuilt')

    def mirror(self, mirror_axis='X'):
        """ Mirrors the mesh

        Args:
            mirror_axis: Axis to mirror the mesh on.  Accepts X, Y or Z.  Default: X
        """
        assert mirror_axis in ['X', 'Y', 'Z'], "Expected character 'X', 'Y' or 'Z'"
        logger.info('Mirroring mesh {} along {} axis'.format(self.name, mirror_axis))
        if mirror_axis == 'X':
            for pos in self._pointList:
                pos[0] = -pos[0]
        elif mirror_axis == 'Y':
            for pos in self._pointList:
                pos[1] = -pos[1]
        elif mirror_axis == 'Z':
            for pos in self._pointList:
                pos[2] = -pos[2]

    def is_topologically_corresponding(self):
        """ Compare an in scene mesh, with the one saved in this node.
            TODO: Currently just checks if vert count is same between these two meshes.
            Need to update this to a better method.

        Returns:
            True if topologically corresponding, False otherwise.
        """
        mesh = self.long_name
        if not cmds.objExists(mesh):
            mesh = self.name
        if not cmds.objExists(mesh):
            logger.error("Failed to check mesh {} topoloy info as it doesn't exist.")
            return False

        pt_list = get_mesh_info(mesh)[2]
        return len(pt_list) == len(self._pointList)


def get_mesh_info(mesh_name):
    """ Gets mesh connectivity for given mesh.

    Args:
        mesh_name: Name of mesh to process.

    Returns:
        tuple: tuple of polygon counts, polygon connects, and points.
    """
    mesh_dag_path = get_dag_path_from_mesh(mesh_name)
    mesh_dag_path.extendToShape()

    poly_count_list = []
    poly_connect_list = []
    mesh_poly_iter = om2.MItMeshPolygon(mesh_dag_path)
    while not mesh_poly_iter.isDone():
        poly_connect_array = mesh_poly_iter.getVertices()
        for elem in poly_connect_array:
            poly_connect_list.append(elem)

        poly_count_list.append(len(poly_connect_array))
        # TODO: Remove version check after Maya 2019 retires
        if get_maya_api_version() < 20200000:
            mesh_poly_iter.next(mesh_poly_iter)
        else:
            mesh_poly_iter.next()

    # Get mesh vertex position
    mesh_name = get_name_from_mobject(mesh_dag_path)
    poly_vertex_list = cmds.xform(mesh_name + '.vtx[*]', q=True, ws=True, t=True)
    assert len(
        poly_vertex_list) % 3 == 0, 'Mesh vertex position list size is not a multiplier of 3.'
    # convert flat list of points to list containing 3 element lists.
    # Each 3 element list is x, y, z worldspace coordinate of vert.
    poly_vertex_list = [poly_vertex_list[x:x + 3] for x in range(0, len(poly_vertex_list), 3)]

    return poly_count_list, poly_connect_list, poly_vertex_list
