import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

import zBuilder.zMaya as mz
from zBuilder.data import BaseComponent
import logging

logger = logging.getLogger(__name__)


class Map(BaseComponent):
    type = 'map'

    def __init__(self, *args, **kwargs):
        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._name = None
        self._mesh = None
        self.value = None

        BaseComponent.__init__(self, *args, **kwargs)
        if args:
            map_name = args[0]
            mesh_name = args[1]

            if map_name and mesh_name:
                self.populate(map_name, mesh_name)

    def __str__(self):
        name = self.name
        if self.value:
            length = len(self.value)
        else:
            length = 'null'
        output = ''
        output += '< MAP: {} -- length: {} >'.format(name, length)
        return output

    def __repr__(self):
        name = self.name
        if self.value:
            length = len(self.value)
        else:
            length = 'null'
        output = ''
        output += '< MAP: {} -- length: {} >'.format(name, length)
        return output

    def populate(self, map_name, mesh_name):
        """ Populate node with that from the maya scene.

        Args:
            map_name: Name of map to populate it with.
            mesh_name: Name of mesh to populate it with.

        """
        weight_value = get_weights(map_name, mesh_name)

        self.name = map_name
        self.set_mesh(mesh_name)
        self.type = 'map'
        self.value = weight_value

        # logger.info('Retrieving Data : {}'.format(self))

    def set_mesh(self, mesh):
        """ Stores the mesh name.

        Args:
            mesh: The mesh name to store.
        """
        self._mesh = mesh   

    def get_mesh(self, long_name=False):
        """ Gets the stores name of the mesh associated with map.

        Args:
            long_name: Returns long name.  Default to ``False``

        Returns:
            Name of mesh.

        """
        if self._mesh:
            if long_name:
                return self._mesh
            else:
                return self._mesh.split('|')[-1]
        else:
            return None

    def get_mesh_data(self):
        """ Gets the mesh data object.

        Returns:
            zBuilder data object of mesh.
        """
        mesh_name = self.get_mesh(long_name=False)
        mesh_data = self._setup.get_data(type_filter='mesh',
                                         name_filter=mesh_name)[0]
        return mesh_data

    def is_topologically_corresponding(self):
        """ Checks if mesh ih data object is corresponding with mesh in scene.

        Returns:
            True if they are, else False.
        """
        mesh_data = self.get_mesh_data()[0]
        return mesh_data.is_topologically_corresponding()

    def interpolate(self):
        """ Interpolates map against mesh in scene.  Re-sets value."""
        mesh_data = self.get_mesh_data()
        logger.info('interpolating map:  {}'.format(self.name))
        created_mesh = mesh_data.build()
        weight_list = interpolate_values(created_mesh,
                                         mesh_data.name,
                                         self.value)
        self.value = weight_list
        mc.delete(created_mesh)


def get_weights(map_name, mesh_name):
    """ Gets the weights for the map.
    Args:
        map_name: Map to get weights from.
        mesh_name: Mesh to check vert count.

    Returns:
        value of map

    Raises:
        ValueError: if there is a problem getting map.
    """
    vert_count = mc.polyEvaluate(mesh_name, v=True)
    try:
        value = mc.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
    except ValueError:
        value = mc.getAttr(map_name)
    return value


def interpolate_values(source_mesh, destination_mesh, weight_list):
    """
    Description:
        Will transfer values between similar meshes with differing topology.
        Lerps values from triangleIndex of closest point on mesh.

    Accepts:
        sourceMeshName, destinationMeshName - strings for each mesh transform

    Returns:

    """
    source_mesh_m_dag_path = mz.get_mdagpath_from_mesh(source_mesh)
    destination_mesh_m_dag_path = mz.get_mdagpath_from_mesh(destination_mesh)
    source_mesh_shape_m_dag_path = om.MDagPath(source_mesh_m_dag_path)
    source_mesh_shape_m_dag_path.extendToShape()

    source_mesh_m_mesh_intersector = om.MMeshIntersector()
    source_mesh_m_mesh_intersector.create(source_mesh_shape_m_dag_path.node())

    destination_mesh_m_it_mesh_vertex = om.MItMeshVertex(
        destination_mesh_m_dag_path)
    source_mesh_m_it_mesh_polygon = om.MItMeshPolygon(source_mesh_m_dag_path)

    u_util = om.MScriptUtil()
    v_util = om.MScriptUtil()
    u_util_ptr = u_util.asFloatPtr()
    v_util_ptr = v_util.asFloatPtr()

    int_util = om.MScriptUtil()

    interpolated_weights = list()

    while not destination_mesh_m_it_mesh_vertex.isDone():

        closest_m_point_on_mesh = om.MPointOnMesh()
        source_mesh_m_mesh_intersector.getClosestPoint(
            destination_mesh_m_it_mesh_vertex.position(om.MSpace.kWorld),
            closest_m_point_on_mesh
        )

        source_mesh_m_it_mesh_polygon.setIndex(
            closest_m_point_on_mesh.faceIndex(),
            int_util.asIntPtr()
        )
        triangle_m_point_array = om.MPointArray()
        triangle_m_int_array = om.MIntArray()

        source_mesh_m_it_mesh_polygon.getTriangle(
            closest_m_point_on_mesh.triangleIndex(),
            triangle_m_point_array,
            triangle_m_int_array,
            om.MSpace.kWorld
        )

        closest_m_point_on_mesh.getBarycentricCoords(
            u_util_ptr,
            v_util_ptr
        )

        weights = list()
        for i in xrange(3):
            vertex_id_int = triangle_m_int_array[i]
            weights.append(weight_list[vertex_id_int])

        bary_u = u_util.getFloat(u_util_ptr)
        bary_v = v_util.getFloat(v_util_ptr)
        bary_w = 1 - bary_u - bary_v

        interp_weight = (bary_u * weights[0]) + (bary_v * weights[1]) + (
            bary_w * weights[2])

        interpolated_weights.append(interp_weight)

        destination_mesh_m_it_mesh_vertex.next()

    return interpolated_weights


