import json
import inspect
import sys
import logging

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


def pack_zbuilder_contents(json_data, type_filter=[], invert_match=False):
    """ Utility wrapper to identify data.

    Args:
    json_data:
    """
    logger.info("packing zBuilder contents for json.")

    node_data = dict()
    node_data['d_type'] = 'node_data'
    node_data['data'] = json_data.get_scene_items(type_filter=type_filter,
                                                  invert_match=invert_match)

    info = dict()
    info['d_type'] = 'info'
    info['data'] = json_data.info

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


def dump_json(file_path, json_data):
    """ Saves a json file to disk given a file path and data.

    Args:
        file_path: The location to save the json file.
        json_data: The data to save in the json.

    Returns:
        file path if successful.

    Raises:
        IOError: If not able to write file.
    """
    try:
        with open(file_path, 'w') as outfile:
            json.dump(json_data,
                      outfile,
                      cls=BaseNodeEncoder,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))
    except IOError:
        logger.error("Error: can\'t find file or write data")
    else:
        return file_path


def load_json(file_path):
    """ loads a json file from disk given a file path.

    Args:
        file_path: The location to save the json file.

    Returns:
        json data

    Raises:
        IOError: If not able to read file.
    """
    try:
        with open(file_path, 'rb') as handle:
            json_data = json.load(handle, object_hook=load_base_node)
    except IOError:
        logger.error("Error: can\'t find file or read data")
    else:
        return json_data


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
        module_ = json_object['_class'][0]
        type_ = json_object.get('type', 'Base')

        builder_type = json_object['_builder_type']
        obj = find_class(builder_type, type_)

        # this catches the scene items for ui that slip in.
        try:
            scene_item = obj(deserialize=json_object)
            return scene_item
        except TypeError:
            return json_object

    else:
        return json_object


# TODO builder and this use same method
def find_class(module_, type_):
    """ Given a module and a type returns class object.

    Args:
        module_ (:obj:`str`): The module to look for.
        type_ (:obj:`str`): The type to look for.

    Returns:
        obj: class object.
    """
    for name, obj in inspect.getmembers(sys.modules[module_]):
        if inspect.isclass(obj):
            if obj.TYPES:
                if type_ in obj.TYPES:
                    return obj
            if type_ == obj.type:
                return obj
