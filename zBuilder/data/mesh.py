import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import maya.OpenMaya as om
from zBuilder.data import BaseComponent
import logging

logger = logging.getLogger(__name__)


class Mesh(BaseComponent):
    TYPE = 'mesh'

    def __init__(self, *args, **kwargs):
        self._class = (self.__class__.__module__, self.__class__.__name__)
        self._name = None
        self._pCountList = []
        self._pConnectList = []
        self._pointList = []

        BaseComponent.__init__(self, *args, **kwargs)

        if args:
            mesh_name = args[0]
            if mesh_name:
                self.populate(mesh_name)

    def __str__(self):
        name = self.get_name(long_name=True)
        poly = len(self.get_polygon_counts())
        vert = len(self.get_point_list())
        output = ''
        output += '< MESH: {} -- Poly: {}  Vert: {} >'.format(name, poly, vert)
        return output

    def __repr__(self):
        return self.__str__()

    def populate(self, mesh_name):
        """

        Args:
            mesh_name: Name of mesh to populate node with.

        Returns:

        """
        connectivity = mz.get_mesh_connectivity(mesh_name)

        self.set_name(mesh_name)
        self.set_type('mesh')
        self.set_polygon_counts(connectivity['polygonCounts'])
        self.set_polygon_connects(connectivity['polygonConnects'])
        self.set_point_list(connectivity['points'])

        logger.info('Retrieving Data : {}'.format(self))

    def string_replace(self, search, replace):
        # name replace----------------------------------------------------------
        name = self.get_name(long_name=True)
        newName = mz.replace_long_name(search, replace, name)
        self.set_name(newName)

    def set_polygon_counts(self, pCountList):
        self._pCountList = pCountList

    def set_polygon_connects(self, pConnectList):
        self._pConnectList = pConnectList

    def set_point_list(self, point_list):
        self._pointList = point_list

    def get_polygon_counts(self):
        return self._pCountList

    def get_polygon_connects(self):
        return self._pConnectList

    def get_point_list(self):
        return self._pointList

    def build(self):
        mesh = build_mesh(
            self.get_name(),
            self.get_polygon_counts(),
            self.get_polygon_connects(),
            self.get_point_list(),
        )
        return mesh

    def mirror(self):
        pl = self.get_point_list()
        tmp = []
        for item in pl:
            tmp.append([-item[0], item[1], item[2]])
        self.set_point_list(tmp)

    def is_topologically_corrispoding(self):
        """
        Compare a mesh in scene with one saved in this node.  Currently just
        checking if vert count is same.  Need to update this to a better method.

        Args:

        Returns: True if topologically corrisponding

        """
        cur_conn = mz.get_mesh_connectivity(self.get_name())

        if len(cur_conn['points']) == len(self.get_point_list()):
            return True
        return False


def build_mesh(name, polygonCounts, polygonConnects, vertexArray):
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
    returned = newMesh_mfnMesh.create(newPointArray.length(),
                                      polygonCounts_mIntArray.length(),
                                      newPointArray,
                                      polygonCounts_mIntArray,
                                      polygonConnects_mIntArray)

    returned_mfnDependencyNode = om.MFnDependencyNode(returned)

    # do housekeeping. 
    returnedName = returned_mfnDependencyNode.name()

    rebuiltMesh = mc.rename(returnedName, name + '_rebuilt')

    # mc.sets( rebuiltMesh, e=True, addElement='initialShadingGroup' )

    return rebuiltMesh

