__version__ = '1.1.0'

from datetime import datetime
import logging
import os
from tempfile import gettempdir

# Setup logging file and output level
cur_time = datetime.now()
log_file_path = os.path.join(gettempdir(),
                             'zBuilder_{}.log'.format(cur_time.strftime('%Y-%m-%d_%H-%M-%S')))
handler = logging.FileHandler(log_file_path)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.info('Logging to file: "{}"'.format(log_file_path))

# Maya default logging output level is info.
# Swtich to debug level when ZIVA_ZBUILDER_DEBUG is defined.
if 'ZIVA_ZBUILDER_DEBUG' in os.environ:
    logger.setLevel(logging.DEBUG)
