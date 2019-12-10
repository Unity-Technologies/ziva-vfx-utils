import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

import zBuilder.zMaya as mz
from zBuilder.nodes.base import Base
import logging

logger = logging.getLogger(__name__)


class Map(Base):
    type = 'map'

    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        self._mesh = None
        #: list of str: Doc comment *before* attribute, with type specified
        self.values = None
        """str: Docstring *after* attribute, with type specified."""

        self.map_type = None

        if args:
            map_name = args[0]
            mesh_name = args[1]

            if map_name and mesh_name:
                self.populate(map_name, mesh_name)

    def __str__(self):
        if self.name:
            name = self.name
            output = ''
            output += '= {} <{} {}> ==================================\n'.format(
                name, self.__class__.__module__, self.__class__.__name__)
            for key in self.__dict__:
                if key == 'values':
                    output += '\t{} - [{},....]\n'.format(key, self.__dict__[key][0])
                else:
                    output += '\t{} - {}\n'.format(key, self.__dict__[key])
            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        name = self.name
        if self.values:
            length = len(self.values)
        else:
            length = 'null'
        output = ''
        output += '< MAP: {} -- length: {} >'.format(name, length)
        return output

    def populate(self, map_name=None, mesh_name=None):
        """ Populate node with that from the maya scene.

        Args:
            map_name: Name of map to populate it with.
            mesh_name: Name of mesh to populate it with.

        """
        map_type = mc.objectType(map_name)
        weight_value = get_weights(map_name, mesh_name)

        self.name = map_name
        self.set_mesh(mesh_name)
        self.type = 'map'
        self.values = weight_value
        self.map_type = map_type

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

    def get_mesh_component(self):
        """ Gets the mesh data object.

        Returns:
            zBuilder data object of mesh.
        """
        mesh_name = self.get_mesh(long_name=False)
        mesh_data = self.builder.get_scene_items(type_filter='mesh', name_filter=mesh_name)[0]
        return mesh_data

    def is_topologically_corresponding(self):
        """ Checks if mesh ih data object is corresponding with mesh in scene.

        Returns:
            True if they are, else False.
        """
        mesh_data = self.get_mesh_component()
        return mesh_data.is_topologically_corresponding()

    def interpolate(self):
        """ Interpolates map against mesh in scene.  Re-sets value."""
        mesh_data = self.get_mesh_component()

        if mc.objExists(mesh_data.name):
            logger.info('interpolating map:  {}'.format(self.name))
            created_mesh = mesh_data.build_mesh()
            weight_list = interpolate_values(created_mesh, mesh_data.name, self.values)
            self.values = weight_list

            mc.delete(created_mesh)

    def invert(self):
        """Invert the map.
        """
        self.values = invert_weights(self.values)

    def apply_weights(self):
        """This applies the weight from this node to the maya scene.
        """
        if mc.objExists('%s[0]' % self.name):
            if not mc.getAttr('%s[0]' % self.name, l=True):
                val = ' '.join([str(w) for w in self.values])
                cmd = "setAttr {}[0:{}] {}".format(self.name, len(self.values) - 1, val)
                mm.eval(cmd)
        else:
            # applying doubleArray maps
            if mc.objExists(self.name):
                mc.setAttr(self.name, self.values, type='doubleArray')

    def copy_values_from(self, map_parameter):
        self.values = map_parameter.values

    def paint_weights(self, node):
        """Open paint tool for the map
        Args:
            node (zBuilder object): zBuilder.nodes object
        """
        # sourcing the mel command so we have access to it
        mm.eval('source "artAttrCreateMenuItems"')

        mc.select(self._mesh, r=True)
        # get map name without node name
        map_name = self.name.split(".")[-1]
        cmd = 'artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}" );'.format(
            self.map_type, node.long_name, map_name)
        mm.eval(cmd)

def invert_weights(weights):
    """This inverts maps so a 1 becomes a 0 and a .4 becomes a .6 for example.  
    
    Args:
        weights (list): Weight list, a list of floats or ints.
    
    Returns:
        list: list of floats
    """
    weights = [1.0 - x for x in weights]
    return weights


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


def interpolate_values(source_mesh, destination_mesh, weight_list, clamp=[0, 1]):
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

    destination_mesh_m_it_mesh_vertex = om.MItMeshVertex(destination_mesh_m_dag_path)
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
            destination_mesh_m_it_mesh_vertex.position(om.MSpace.kWorld), closest_m_point_on_mesh)

        source_mesh_m_it_mesh_polygon.setIndex(closest_m_point_on_mesh.faceIndex(),
                                               int_util.asIntPtr())
        triangle_m_point_array = om.MPointArray()
        triangle_m_int_array = om.MIntArray()

        source_mesh_m_it_mesh_polygon.getTriangle(closest_m_point_on_mesh.triangleIndex(),
                                                  triangle_m_point_array, triangle_m_int_array,
                                                  om.MSpace.kWorld)

        closest_m_point_on_mesh.getBarycentricCoords(u_util_ptr, v_util_ptr)

        weights = list()
        for i in xrange(3):
            vertex_id_int = triangle_m_int_array[i]
            weights.append(weight_list[vertex_id_int])

        bary_u = u_util.getFloat(u_util_ptr)
        bary_v = v_util.getFloat(v_util_ptr)
        bary_w = 1 - bary_u - bary_v

        interp_weight = (bary_u * weights[0]) + (bary_v * weights[1]) + (bary_w * weights[2])
        interpolated_weights.append(interp_weight)

        destination_mesh_m_it_mesh_vertex.next()

    # clamp the values if needed
    if clamp:
        interpolated_weights = [max(min(x, clamp[1]), clamp[0]) for x in interpolated_weights]

    return interpolated_weights
