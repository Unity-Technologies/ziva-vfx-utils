import logging
import os

from datetime import datetime
from tempfile import gettempdir

# zBuilder library version number
__version__ = "2.1.0"

# Setup logging file and output level
cur_time = datetime.now()
log_file_path = os.path.join(gettempdir(),
                             "zBuilder_{}.log".format(cur_time.strftime("%Y-%m-%d_%H-%M-%S")))
handler = logging.FileHandler(log_file_path)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.info("Logging to file: \"{}\"".format(log_file_path))

# Maya default logging output level is info.
# Switch to debug level when ZIVA_ZBUILDER_DEBUG is defined.
if "ZIVA_ZBUILDER_DEBUG" in os.environ:
    logger.setLevel(logging.DEBUG)
