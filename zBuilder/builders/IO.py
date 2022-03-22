import json
import logging

from zBuilder.updates import update_json_pre_1_0_11
from zBuilder.utils import parse_version_info
from .builder import find_class

logger = logging.getLogger(__name__)


class BaseNodeEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '_class'):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            else:
                return obj.__dict__
        else:
            return super(BaseNodeEncoder, self).default(obj)


def pack_zbuilder_contents(builder, type_filter, invert_match):
    """ Utility to package the data in a dictionary.
    """
    logger.info("packing zBuilder contents for json.")

    node_data = dict()
    node_data['d_type'] = 'node_data'
    node_data['data'] = builder.get_scene_items(type_filter=type_filter, invert_match=invert_match)

    info = dict()
    info['d_type'] = 'info'
    info['data'] = builder.info

    return [node_data, info]


def unpack_zbuilder_contents(builder, json_data):
    """ Gets data out of json serialization and assigns it to node collection
    object.

    Args:
        json_data: Data to assign to builder object.
    """
    for d in json_data:
        if d['d_type'] == 'node_data':
            builder.bundle.extend_scene_items(d['data'])
            logger.info("Reading scene items. {} nodes".format(len(d['data'])))

        if d['d_type'] == 'info':
            builder.info = d['data']
            logger.info("Reading info.")

    logger.info("Assigning builder.")
    for item in builder.bundle:
        if item:
            item.builder = builder


def load_base_node(json_object):
    """
    Loads json objects into proper classes.  Serves as object hook for loading
    json.

    Args:
        json_object (obj): json obj to perform action on

    Returns:
        obj:  Result of operation
    """
    if '_class' in json_object:
        major, minor, patch, _ = parse_version_info(json_object['info']['version'])
        # For pre zBuilder 1.0.11 file format, we need to parameter reference to each node
        if (major, minor, patch) < (1, 0, 11):
            update_json_pre_1_0_11(json_object)

        obj = find_class(json_object['_builder_type'], json_object.get('type', 'Base'))
        try:
            scene_item = obj()
            scene_item.deserialize(json_object)
            return scene_item
        except TypeError:
            # Catches the scene items for ui that slip in.
            return json_object

    return json_object
