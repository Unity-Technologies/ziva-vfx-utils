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


def wrap_data(data, type_):
    """ Utility wrapper to identify data.

    Args:
        data:
        type_ (:obj:`str`): The type of data it is.
    """
    wrapped = dict()
    wrapped['d_type'] = type_
    wrapped['data'] = data
    return wrapped


def dump_json(file_path, json_data):
    try:
        with open(file_path, 'w') as outfile:
            json.dump(json_data, outfile, cls=BaseNodeEncoder,
                      sort_keys=True, indent=4, separators=(',', ': '))
    except IOError:
        logger.error("Error: can\'t find file or write data")
    else:
        return file_path


def load_json(file_path):
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

    update_json(json_object)

    if '_class' in json_object:
        module_ = json_object['_class'][0]

        type_ = json_object['type']
        if 'zBuilder.data' in module_:
            obj = find_class('zBuilder.data', type_)
        elif 'zBuilder.nodes' in module_:
            obj = find_class('zBuilder.nodes', type_)

        b_node = obj(deserialize=json_object)
        return b_node
    else:
        return json_object


def find_class(module_, type_):
    """ Given a module and a type returns class object.

    Args:
        module_ (:obj:`str`): The module to look for.
        type_ (:obj:`str`): The type to look for.

    Returns:
        obj: class object.
    """
    for name, obj in inspect.getmembers(
            sys.modules[module_]):
        if inspect.isclass(obj):
            print type_, obj.type
            if type_ == obj.type:
                return obj


def update_json(json_object):
    """
    This takes the json_object and updates it to work with 1.0.0

    Returns:
        modified json_object
    """

    # replacing key attribute names with value.  A simple swap.
    replace_me = dict()
    replace_me['_type'] = 'TYPE'
    replace_me['_attrs'] = 'attrs'
    replace_me['_value'] = 'values'
    replace_me['__collection'] = 'nodes'
    replace_me['_zFiber'] = 'fiber'

    if '_class' in json_object:

        for key, value in replace_me.iteritems():
            if key in json_object:
                json_object[value] = json_object[key]
                json_object.pop(key, None)
            else:
                # print 'NOPE', value, json_object.keys()
                # maps and meshes didn't have a type.  lets make one.
                if value == 'TYPE':
                    json_object[value] = json_object['_class'][1].lower()

    return json_object


def check_data(data):
    """ Utility to check data format after loaded from josn.  Used to check if
    data is wrapped in dictionary.  If it isn't it wraps it.  Used to deal with
    older zBuilder files.

    Args:
        data: Data to check.

    Returns:
        Result of operation.
    """
    if 'd_type' in data[0]:
        return data
    else:
        tmp = list()
        tmp.append(wrap_data(data[0], 'node_data'))
        tmp.append(wrap_data(data[1], 'component_data'))
        if len(data) == 3:
            tmp.append(wrap_data(data[2], 'info'))
        return tmp


