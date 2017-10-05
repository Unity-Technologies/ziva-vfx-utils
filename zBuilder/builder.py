from zBuilder.nodeCollection import NodeCollection
from zBuilder.IO import IO

import zBuilder.zMaya as mz
import zBuilder.data
import zBuilder.nodes
from functools import wraps
import datetime
import sys
import inspect
import logging

logger = logging.getLogger(__name__)


class Builder(IO, NodeCollection):
    """ The main class for using zBuilder.

    This inherits from nodeCollection which is a glorified list.
    """
    def __init__(self):
        NodeCollection.__init__(self)

    def node_factory(self, node):
        """Given a maya node, this checks objType and instantiats the proper
        zBuilder.node and populates it and returns it.

        Args:
            node (:obj:`str`): Name of maya node.

        Returns:
            obj: zBuilder node populated.
        """
        type_ = mz.get_type(node)
        for name, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
            if inspect.isclass(obj):
                if obj.TYPES:
                    if type_ in obj.TYPES:
                        return obj(node, setup=self)
                if type_ == obj.type:
                    return obj(node, setup=self)
        return zBuilder.nodes.BaseNode(node, setup=self)

    def component_factory(self, *args, **kwargs):
        """ This instantiates and populates a zBuilder data node based on type.
        Since we can't check type against what is passed we need to pass type
        explicitly.  As of writing type is either map or mesh.
        Args:
            args: args get passed directly to node instantiation.
            type (:obj:`str`): Type of data node to instantiate.

        Returns:
            obj: zBuilder data node populated.
        """
        type_ = kwargs.get('type', True)

        for name, obj in inspect.getmembers(sys.modules['zBuilder.data']):
            if inspect.isclass(obj):
                if type_ == obj.type:
                    return obj(*args, setup=self)

    @staticmethod
    def time_this(original_function):
        """
        A decorator to time functions.
        """
        @wraps(original_function)
        def new_function(*args, **kwargs):
            before = datetime.datetime.now()
            x = original_function(*args, **kwargs)
            after = datetime.datetime.now()
            logger.info("Finished: ---Elapsed Time = {0}".format(after - before))
            return x

        return new_function


