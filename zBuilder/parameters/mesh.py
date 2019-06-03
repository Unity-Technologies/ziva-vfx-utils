import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import maya.OpenMaya as om
from zBuilder.nodes.base import Base
import logging

logger = logging.getLogger(__name__)


class Mesh(Base):
    type = 'mesh'
    """ Type of node. """

    def __init__(self, *args, **kwargs):
        self._pCountList = []
        self._pConnectList = []
        self._pointList = []

        Base.__init__(self, *args, **kwargs)
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
        connectivity = get_mesh_connectivity(mesh_name)

        self.name = mesh_name
        self.type = 'mesh'
        self.set_polygon_counts(connectivity['polygonCounts'])
        self.set_polygon_connects(connectivity['polygonConnects'])
        self.set_point_list(connectivity['points'])

        # logger.info('Retrieving Data : {}'.format(self))

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
        if mc.objExists(self.name):
            cur_conn = mz.get_mesh_connectivity(self.name)

            if len(cur_conn['points']) == len(self.get_point_list()):
                return True
            return False
        else:
            return None


def get_mesh_connectivity(mesh_name):
    """ Gets mesh connectivity for given mesh.

    Args:
        mesh_name: Name of mesh to process.

    Returns:
        dict: Dictionary of polygonCounts, polygonConnects, and points.
    """
    space = om.MSpace.kWorld
    mesh_to_rebuild_m_dag_path = mz.get_mdagpath_from_mesh(mesh_name)
    mesh_to_rebuild_m_dag_path.extendToShape()

    mesh_to_rebuild_poly_iter = om.MItMeshPolygon(mesh_to_rebuild_m_dag_path)
    mesh_to_rebuild_vert_iter = om.MItMeshVertex(mesh_to_rebuild_m_dag_path)

    num_polygons = 0
    num_vertices = 0
    # vertexArray_mFloatPointArray = om.MFloatPointArray()
    # polygonCounts_mIntArray = om.MIntArray()
    polygon_counts_list = list()
    polygon_connects_list = list()
    point_list = list()

    while not mesh_to_rebuild_vert_iter.isDone():
        num_vertices += 1
        pos_m_point = mesh_to_rebuild_vert_iter.position(space)
        pos_m_float_point = om.MFloatPoint(pos_m_point.x, pos_m_point.y, pos_m_point.z)

        point_list.append([pos_m_float_point[0], pos_m_float_point[1], pos_m_float_point[2]])
        mesh_to_rebuild_vert_iter.next()

    while not mesh_to_rebuild_poly_iter.isDone():
        num_polygons += 1
        polygon_vertices_m_int_array = om.MIntArray()
        mesh_to_rebuild_poly_iter.getVertices(polygon_vertices_m_int_array)
        for vertexIndex in polygon_vertices_m_int_array:
            polygon_connects_list.append(vertexIndex)

        polygon_counts_list.append(polygon_vertices_m_int_array.length())

        mesh_to_rebuild_poly_iter.next()
    tmp = dict()
    tmp['polygonCounts'] = polygon_counts_list
    tmp['polygonConnects'] = polygon_connects_list
    tmp['points'] = point_list

    return tmp


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
    polygonCounts_mIntArray = om.MIntArray()
    polygonConnects_mIntArray = om.MIntArray()
    vertexArray_mFloatPointArray = vertexArray

    for i in polygonCounts:
        polygonCounts_mIntArray.append(i)

    for i in polygonConnects:
        polygonConnects_mIntArray.append(i)

    # back
    newPointArray = om.MPointArray()
    for point in vertexArray_mFloatPointArray:
        newPoint = om.MPoint(point[0], point[1], point[2], 1.0)
        newPointArray.append(newPoint)

    newMesh_mfnMesh = om.MFnMesh()
    returned = newMesh_mfnMesh.create(newPointArray.length(), polygonCounts_mIntArray.length(),
                                      newPointArray, polygonCounts_mIntArray,
                                      polygonConnects_mIntArray)

    returned_mfnDependencyNode = om.MFnDependencyNode(returned)

    # do housekeeping.
    returnedName = returned_mfnDependencyNode.name()

    rebuiltMesh = mc.rename(returnedName, name + '_rebuilt')

    # mc.sets( rebuiltMesh, e=True, addElement='initialShadingGroup' )

    return rebuiltMesh
