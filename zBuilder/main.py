from zBuilder.nodeCollection import NodeCollection

from functools import wraps

import datetime

import logging

logger = logging.getLogger(__name__)


class Builder(NodeCollection):
    def __init__(self):
        NodeCollection.__init__(self)


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
