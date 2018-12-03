#############################################
# Device connection infrastructure
#############################################

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


class DcommError(Exception):
    pass
