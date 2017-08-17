from zBuilder.nodeCollection import NodeCollection
import zBuilder.nodes
import zBuilder.zMaya as mz
from zBuilder.data import Map
from zBuilder.data import Mesh

from functools import wraps
import datetime
import sys
import inspect
import logging

logger = logging.getLogger(__name__)


class Builder(NodeCollection):
    def __init__(self):
        NodeCollection.__init__(self)

    @staticmethod
    def node_factory(node):
        """

        Args:
            node:

        Returns:

        """
        type_ = mz.get_type(node)
        for name, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):

            if inspect.isclass(obj):
                if type_ == obj.TYPE:
                    return obj(node)

        return zBuilder.nodes.BaseNode(node)

    @staticmethod
    def component_factory(*args):
        """

        Args:
            *args:

        Returns:

        """
        type_ = args[0]
        for name, obj in inspect.getmembers(sys.modules['zBuilder.data']):
            if inspect.isclass(obj):
                if type_ == obj.TYPE:
                    return obj(*args[1:])

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


