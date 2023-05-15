import logging
from maya import cmds
from maya import mel
from maya.api import OpenMaya as om2

from zBuilder.utils.paintable_maps import get_paintable_map, set_paintable_map, split_map_name
from zBuilder.utils.commonUtils import clamp
from zBuilder.utils.mayaUtils import get_short_name, get_dag_path_from_mesh, get_type, invert_weights
from ..base import Base

logger = logging.getLogger(__name__)


class Map(Base):
    type = 'map'

    # This is an inherited class attribute.
    SEARCH_EXCLUDE = Base.SEARCH_EXCLUDE + ['map_type', 'interp_method']

    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)

        # Name of mesh associated with map
        self._mesh = None
        # a list of values for the map
        self.values = None
        # Type of Ziva VFX map  (zAttachment, zTet, zMaterial, zFiber)
        self.map_type = None
        # The interpolation method for map (barycentric, endPoints)
        self.interp_method = None

        if args:
            map_name = args[0]
            mesh_name = args[1]
            self.interp_method = args[2]
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
                    if self.values:
                        output += '\t{} - [{},....]\n'.format(key, self.__dict__[key][0])
                    else:
                        output += '\t{} - Not retrieved yet\n'.format(key)
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
        self.name = map_name
        self.set_mesh(mesh_name)
        self.type = 'map'
        self.map_type = get_type(map_name)
        # Defer retrieve map value to retrieve_values() until it is needed.

    def retrieve_values(self):
        """ get the values of the map from the scene and update the scene_item
        """
        split_map = split_map_name(self.long_name)
        self.values = get_paintable_map(split_map[0], split_map[1], self.get_mesh(long_name=True))

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
            return get_short_name(self._mesh)
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

        mesh_name = mesh_data.long_name
        if not cmds.objExists(mesh_name):
            mesh_name = mesh_data.name
        if cmds.objExists(mesh_name):
            logger.info('interpolating map:  {}'.format(self.name))
            created_mesh = mesh_data.build_mesh()
            interp_weights = self.values
            if self.interp_method == "barycentric":
                interp_weights = interpolate_values(created_mesh, mesh_name, self.values)
            elif self.interp_method == "endPoints":
                interp_weights = interpolate_end_points_weights(created_mesh, mesh_name,
                                                                self.values)
            else:
                assert False, "Unknown interpolation method: {}.".format(self.interp_method)

            self.values = interp_weights

            cmds.delete(created_mesh)

    def invert(self):
        """ Invert the map.
        """
        self.values = invert_weights(self.values)

    def apply_weights(self):
        """This applies the weight from this node to the maya scene.
        """
        node, attr = split_map_name(self.name)
        set_paintable_map(node, attr, self.values)

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




def interpolate_values(source_mesh, destination_mesh, weight_list, clamp_range=[0, 1]):
    """
    Description:
        Will transfer values between similar meshes with differing topology.
        Lerps values from triangleIndex of closest point on mesh.

    Accepts:
        sourceMeshName, destinationMeshName - strings for each mesh transform

    Returns:
        list(float)
    """
    src_mesh_dag_path = get_dag_path_from_mesh(source_mesh)
    src_shape_dag_path = om2.MDagPath(src_mesh_dag_path)
    src_shape_dag_path.extendToShape()

    src_mesh_intersector = om2.MMeshIntersector()
    src_mesh_intersector.create(src_shape_dag_path.node(), src_mesh_dag_path.inclusiveMatrix())

    dst_mesh_dag_path = get_dag_path_from_mesh(destination_mesh)
    dst_mesh_vtx_iter = om2.MItMeshVertex(dst_mesh_dag_path)
    src_mesh_poly_iter = om2.MItMeshPolygon(src_mesh_dag_path)

    interpolated_weights = list()
    while not dst_mesh_vtx_iter.isDone():
        closest_point_on_src_mesh = src_mesh_intersector.getClosestPoint(
            dst_mesh_vtx_iter.position(om2.MSpace.kWorld))
        src_mesh_poly_iter.setIndex(closest_point_on_src_mesh.face)
        _, triangle_m_int_array = src_mesh_poly_iter.getTriangle(closest_point_on_src_mesh.triangle,
                                                                 om2.MSpace.kWorld)

        weights = list()
        for i in range(3):
            vertex_id_int = triangle_m_int_array[i]
            weights.append(weight_list[vertex_id_int])

        bary_u, bary_v = closest_point_on_src_mesh.barycentricCoords
        bary_w = 1 - bary_u - bary_v

        interp_weight = (bary_u * weights[0]) + (bary_v * weights[1]) + (bary_w * weights[2])
        interpolated_weights.append(interp_weight)

        dst_mesh_vtx_iter.next()

    # clamp the values if needed
    if clamp_range:
        interpolated_weights = [
            clamp(x, clamp_range[0], clamp_range[1]) for x in interpolated_weights
        ]

    return interpolated_weights


def interpolate_end_points_weights(source_mesh, target_mesh, weight_list):
    """ Will transfer values between similar meshes with differing topology.
        Takes value from the closest point on mesh. Works only for zFiber.endPoints map.
        
    Args:
        source_mesh(string): name on the mesh transform to interpolate from
        target_mesh(string): name of the mesh transform to interpolate to
        weight_list(list): weights to interpolate

    Returns:
        list(float)
    """
    tgt_mesh_dag_path = get_dag_path_from_mesh(target_mesh)
    tgt_shape_dag_path = om2.MDagPath(tgt_mesh_dag_path)
    tgt_shape_dag_path.extendToShape()

    tgt_mesh_intersector = om2.MMeshIntersector()
    tgt_mesh_intersector.create(tgt_shape_dag_path.node(), tgt_mesh_dag_path.inclusiveMatrix())

    src_mesh_dag_path = get_dag_path_from_mesh(source_mesh)
    src_mesh_vtx_iter = om2.MItMeshVertex(src_mesh_dag_path)
    tgt_mesh_vtx_iter = om2.MItMeshVertex(tgt_mesh_dag_path)
    tgt_mesh_poly_iter = om2.MItMeshPolygon(tgt_mesh_dag_path)

    # Fill the map with 0.5 values
    interpolated_weights = [0.5] * tgt_mesh_vtx_iter.count()

    while not src_mesh_vtx_iter.isDone():
        current_weight = weight_list[src_mesh_vtx_iter.index()]
        # Round the weight value in [0.9, 1) and [0, 0.1] range
        if current_weight >= 0.9:
            current_weight = 1.0
        elif current_weight <= 0.1:
            current_weight = 0.0

        # Process the weight value is either 0 or 1
        if current_weight in (0, 1):
            # closest polygon
            pos = src_mesh_vtx_iter.position(om2.MSpace.kWorld)
            closest_point_on_src_mesh = tgt_mesh_intersector.getClosestPoint(pos)
            tgt_mesh_poly_iter.setIndex(closest_point_on_src_mesh.face)
            closest_polygon_vtx_array = tgt_mesh_poly_iter.getPoints(om2.MSpace.kWorld)
            closest_polygon_idx_array = tgt_mesh_poly_iter.getVertices()

            # Iterate through vertices on the polygon to get distance sum
            # and distance list to each vertex
            distance_sum = 0
            distance_array = []
            for cur_point in closest_polygon_vtx_array:
                distance = pos.distanceTo(cur_point)
                distance_sum += distance
                distance_array.append(distance)
            average_distance = distance_sum / len(closest_polygon_vtx_array)

            # If distance from projected point to face vertex is
            # equal or less than average distance, set corresponding weight value
            found = False
            for idx, dist in enumerate(distance_array):
                if dist <= average_distance:
                    interpolated_weights[closest_polygon_idx_array[idx]] = current_weight
                    found = True
            # make sure that at least one vertex has a new value
            if not found:
                closest_index = distance_array.index(min(distance_array))
                interpolated_weights[closest_polygon_idx_array[closest_index]] = current_weight

        src_mesh_vtx_iter.next()

    return interpolated_weights
