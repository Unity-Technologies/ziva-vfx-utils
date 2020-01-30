from maya import cmds
from maya import mel
from maya import OpenMaya as om

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
            self.interp_method = args[2]
            self.clamp_values = args[3]
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
        map_type = cmds.objectType(map_name)
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

        if cmds.objExists(mesh_data.name):
            logger.info('interpolating map:  {}'.format(self.name))
            created_mesh = mesh_data.build_mesh()
            interp_weights = self.values
            if self.interp_method == "barycentric":
                interp_weights = interpolate_values(created_mesh, mesh_data.name, self.values,
                                                    self.clamp_values)
            elif self.interp_method == "closest":
                interp_weights = interpolate_values_closest(created_mesh, mesh_data.name,
                                                            self.values, self.clamp_values)
            self.values = interp_weights

            cmds.delete(created_mesh)

    def invert(self):
        """Invert the map.
        """
        self.values = invert_weights(self.values)

    def apply_weights(self):
        """This applies the weight from this node to the maya scene.
        """
        if cmds.objExists('%s[0]' % self.name):
            if not cmds.getAttr('%s[0]' % self.name, l=True):
                val = ' '.join([str(w) for w in self.values])
                cmd = "setAttr {}[0:{}] {}".format(self.name, len(self.values) - 1, val)
                mel.eval(cmd)
        else:
            # applying doubleArray maps
            if cmds.objExists(self.name):
                cmds.setAttr(self.name, self.values, type='doubleArray')

    def copy_values_from(self, map_parameter):
        self.values = map_parameter.values

    def open_paint_tool(self):
        """Open paint tool for the map
        """
        # sourcing the mel command so we have access to it
        mel.eval('source "artAttrCreateMenuItems"')

        cmds.select(self._mesh, r=True)
        # get map name without node name
        map_name = self.name.split(".")[-1]
        # get node name without map name
        node_name = self.name.split(".")[0]
        cmd = 'artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}" );'.format(
            self.map_type, node_name, map_name)
        mel.eval(cmd)


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
    vert_count = cmds.polyEvaluate(mesh_name, v=True)
    try:
        value = cmds.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
    except ValueError:
        value = cmds.getAttr(map_name)
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
    source_mesh_m_mesh_intersector.create(source_mesh_shape_m_dag_path.node(),
                                          source_mesh_m_dag_path.inclusiveMatrix())

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


def interpolate_values_closest(source_mesh, target_mesh, weight_list, clamp=[0, 0.5, 1]):
    """ Will transfer values between similar meshes with differing topology. \
        Takes value from the closest point on mesh.
    Args:
        source_mesh(string): name on the mesh transform to interpolate from
        target_mesh(string): name of the mesh transform to interpolate to
        weight_list(list): weights to interpolate
        clamp(list): values to use for clamping. List size should be 2 or 3.

    Returns:
        list of interpolated weights
    """
    target_mesh_m_dag_path = mz.get_mdagpath_from_mesh(target_mesh)
    source_mesh_m_dag_path = mz.get_mdagpath_from_mesh(source_mesh)
    target_mesh_shape_m_dag_path = om.MDagPath(target_mesh_m_dag_path)
    target_mesh_shape_m_dag_path.extendToShape()

    target_mesh_m_mesh_intersector = om.MMeshIntersector()
    target_mesh_m_mesh_intersector.create(target_mesh_shape_m_dag_path.node(),
                                          target_mesh_m_dag_path.inclusiveMatrix())

    source_mesh_m_it_mesh_vertex = om.MItMeshVertex(source_mesh_m_dag_path)
    target_mesh_m_it_mesh_vertex = om.MItMeshVertex(target_mesh_m_dag_path)
    target_mesh_m_it_mesh_polygon = om.MItMeshPolygon(target_mesh_m_dag_path)

    int_util = om.MScriptUtil()

    interpolated_weights = [clamp[1]] * target_mesh_m_it_mesh_vertex.count()
    while not source_mesh_m_it_mesh_vertex.isDone():
        current_weight = weight_list[source_mesh_m_it_mesh_vertex.index()]
        # in case that weight is in ( 0.99 ... 0.9 ) or ( 0.01 .. 0.1 ) need to round it
        if current_weight not in clamp:
            max_val = max(clamp)
            # allow 10 percent difference but clamp it to the right value
            threshold_val = max_val * 0.1
            for value in clamp:
                if (current_weight <= value + threshold_val) and (current_weight >=
                                                                  value - threshold_val):
                    current_weight = value

        if current_weight in [clamp[0], clamp[-1]]:
            closest_m_point_on_mesh = om.MPointOnMesh()
            pos = source_mesh_m_it_mesh_vertex.position(om.MSpace.kWorld)
            target_mesh_m_mesh_intersector.getClosestPoint(pos, closest_m_point_on_mesh)

            # closest polygon
            target_mesh_m_it_mesh_polygon.setIndex(closest_m_point_on_mesh.faceIndex(),
                                                   int_util.asIntPtr())

            closest_polygon_point_array = om.MPointArray()
            closest_polygon_vtx_id_array = om.MIntArray()

            target_mesh_m_it_mesh_polygon.getPoints(closest_polygon_point_array, om.MSpace.kWorld)
            target_mesh_m_it_mesh_polygon.getVertices(closest_polygon_vtx_id_array)

            distance_sum = pos.distanceTo(closest_polygon_point_array[0])
            distance_array = [distance_sum]
            # iterate through vertices on the polygon and get sum distance and distance to
            # each vertex
            for i in range(1, closest_polygon_point_array.length()):
                distance = pos.distanceTo(closest_polygon_point_array[i])
                distance_sum += distance
                distance_array.append(distance)

            average_distance = distance_sum / closest_polygon_point_array.length()

            # if distance from projected point to face vertex is less or equal then average
            # distance, then store this vertex index to set corresponding weight value
            for i in xrange(closest_polygon_point_array.length()):
                if distance_array[i] <= average_distance:
                    interpolated_weights[closest_polygon_vtx_id_array[i]] = current_weight

        source_mesh_m_it_mesh_vertex.next()

    return interpolated_weights
