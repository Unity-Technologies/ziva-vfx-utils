import logging

from maya import cmds
from maya.api import OpenMaya as om2
from zBuilder.mayaUtils import get_DAG_path_from_mesh, get_name_from_m_object, get_maya_api_version
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
        name = self.long_name
        poly = len(self.get_polygon_counts())
        vert = len(self.get_point_list())
        output = ''
        output += '< MESH: {} -- Poly: {}  Vert: {} >'.format(name, poly, vert)
        return output

    def __repr__(self):
        return self.__str__()

    def populate(self, mesh_name):
        """ Populate node with that from the maya scene.

         Args:
             mesh_name: Name of mesh to populate it with.

        """
        polygon_counts, polygon_connects, points = get_mesh_info(mesh_name)

        self.name = mesh_name
        self.type = 'mesh'
        self.set_polygon_counts(polygon_counts)
        self.set_polygon_connects(polygon_connects)
        self.set_point_list(points)

    def set_polygon_counts(self, pCountList):
        """ Stores the polygon counts.

        Args:
            pCountList (list): The count list.
        """
        self._pCountList = pCountList

    def set_polygon_connects(self, pConnectList):
        """ Stores the polygon connects.

        Args:
            pConnectList (list): The connect list.
        """
        self._pConnectList = pConnectList

    def set_point_list(self, point_list):
        """ Stores the point list.

        Args:
            point_list (list): List of points.
        """
        self._pointList = point_list

    def get_polygon_counts(self):
        """ Get polygon counts. """
        return self._pCountList

    def get_polygon_connects(self):
        """ Get polygon Connects """
        return self._pConnectList

    def get_point_list(self):
        """ Get point List """
        return self._pointList

    def build_mesh(self):
        """ Builds mesh in maya scene.

        Returns:
            mesh name.
        """
        mesh = build_mesh(
            self.name,
            self.get_polygon_counts(),
            self.get_polygon_connects(),
            self.get_point_list(),
        )
        return mesh

    def mirror(self):
        """ Mirrors internal mesh by negating translate X on all points.
        """
        logger.info('Mirroring mesh: {}'.format(self.name))

        value = [[-item[0], item[1], item[2]] for item in self.get_point_list()]
        self.set_point_list(value)

    def is_topologically_corresponding(self):
        """ Compare a mesh in scene with one saved in this node.  Currently just
        checking if vert count is same.  Need to update this to a better method.

        Returns:
            True if topologically corresponding, else False

        """
        mesh = self.long_name
        if not cmds.objExists(mesh):
            mesh = self.name
        if cmds.objExists(mesh):
            points = get_mesh_info(mesh)[2]

            if len(points) == len(self.get_point_list()):
                return True
            return False
        else:
            return None


def get_intermediate(dagPath):
    '''finds the intermediate shape given a dagpath for mesh transform

    Args:
        dagPath (MFnDagPath): dag path for mesh to search for intermediate shape

    Returns:
        mObject: mObject of intermediate shape or None if none found.
    '''

    dag_node = om2.MFnDagNode(dagPath)
    for i in range(dag_node.childCount()):
        child = dag_node.child(i)
        if child.apiType() == om2.MFn.kMesh:
            node = om2.MFnDependencyNode(child)
            intermediate_plug = node.findPlug("intermediateObject", False)
            if intermediate_plug.asBool():
                return child
    return None


def get_mesh_info(mesh_name):
    """ Gets mesh connectivity for given mesh.

    Args:
        mesh_name: Name of mesh to process.

    Returns:
        tuple: tuple of polygonCounts, polygonConnects, and points.
    """
    mesh_to_rebuild_m_dag_path = get_DAG_path_from_mesh(mesh_name)
    intermediate_shape = get_intermediate(mesh_to_rebuild_m_dag_path)
    if intermediate_shape:
        mesh_to_rebuild_m_dag_path = om2.MDagPath.getAPathTo(intermediate_shape)
    else:
        mesh_to_rebuild_m_dag_path.extendToShape()

    mesh_to_rebuild_poly_iter = om2.MItMeshPolygon(mesh_to_rebuild_m_dag_path)
    polygon_counts_list = list()
    polygon_connects_list = list()
    while not mesh_to_rebuild_poly_iter.isDone():
        polygon_vertices_m_int_array = mesh_to_rebuild_poly_iter.getVertices()
        for vertexIndex in polygon_vertices_m_int_array:
            polygon_connects_list.append(vertexIndex)

        polygon_counts_list.append(len(polygon_vertices_m_int_array))
        if get_maya_api_version() < 20200000:
            mesh_to_rebuild_poly_iter.next(mesh_to_rebuild_poly_iter)
        else:
            mesh_to_rebuild_poly_iter.next()

    point_list = get_mesh_vertex_positions(get_name_from_m_object(mesh_to_rebuild_m_dag_path))
    return polygon_counts_list, polygon_connects_list, point_list


def get_mesh_vertex_positions(mesh):
    """Given the name of a mesh, return a list of lists of its world-space vertex positions

    Args:
        mesh (str): The mesh to aquire vertex positions

    Raises:
        Exception: If list cannot be divided by 3

    Returns:
        list of lists: List of vertex positions in x,y, z world positions.
    """
    # See comments here: http://www.fevrierdorian.com/blog/post/2011/09/27/Quickly-retrieve-vertex-positions-of-a-Maya-mesh-%28English-Translation%29
    points = cmds.xform(mesh + '.vtx[*]', q=True, ws=True, t=True)

    # convert flat list of points to list containing 3 element lists.  Each 3 element list is
    # x, y, z worldspace coordinate of vert
    if len(points) % 3 != 0:
        raise Exception('List not divisible by 3.')

    points = [points[x:x + 3] for x in range(0, len(points), 3)]

    return points


def build_mesh(name, polygonCounts, polygonConnects, vertexArray):
    """ Builds mesh in maya scene.
    Args:
        name: Name of mesh.
        polygonCounts: The polygon counts.
        polygonConnects: The polygon connects.
        vertexArray: The point list.

    Returns:
        Name of newly built mesh.

    """
    polygonCounts_mIntArray = om2.MIntArray()
    polygonConnects_mIntArray = om2.MIntArray()
    vertexArray_mFloatPointArray = vertexArray

    for i in polygonCounts:
        polygonCounts_mIntArray.append(i)

    for i in polygonConnects:
        polygonConnects_mIntArray.append(i)

    newPointArray = om2.MPointArray()
    for point in vertexArray_mFloatPointArray:
        newPoint = om2.MPoint(point[0], point[1], point[2], 1.0)
        newPointArray.append(newPoint)

    mesh_fn = om2.MFnMesh()
    newMesh = mesh_fn.create(newPointArray, polygonCounts, polygonConnects)
    # do housekeeping.
    mesh_dep_node = om2.MFnDependencyNode(newMesh)
    new_mesh_name = cmds.rename(mesh_dep_node.name(), name + '_rebuilt')
    return new_mesh_name
