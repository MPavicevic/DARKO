import logging.config
import os

# Importing common functions and version tags
from .common import commons, get_git_revision_tag
from ._version import __version__

# Importing the main DARKO preprocessing functions so that they can be called with "dk.function"
from .preprocessing.data_handler import load_config_excel
from .preprocessing.preprocessing import build_simulation
from .postprocessing.postprocessing import plot_net_positions, get_net_position_plot_data, plot_market_clearing_price, \
    get_marginal_price_plot_data

# Importing the main DARKO solve functions
from .solve import solve_GAMS

# Importing the main postprocessing functions
from .postprocessing.data_handler import get_sim_results, dk_to_df
from .cli import *

# Remove old log file:
for filename in (f for f in os.listdir('.') if f.endswith('.darko.log')):
    try:
        os.remove(filename)
    except OSError:
        print('Could not erase previous log file ' + filename)

# Logging: # TODO: Parametrize in darko cli or external config
_LOGCONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
        'notime': {
            'format': '[%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
    },
    "handlers": {
        "console": {
            "class": "darko.misc.colorstreamhandler.ColorStreamHandler",
            "stream": "ext://sys.stderr",
            #             "stream": "sys.stdout",
            "level": "INFO",
            'formatter': 'notime',
        },

        "error_file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            'formatter': 'standard',
            'filename': commons['logfile'],
            'encoding': 'utf8'

        }
    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "error_file"],
    }
}

# Setting logging configuration:
try:
    logging.config.dictConfig(_LOGCONFIG)
except Exception:
    # if it didn't work, it might be due to ipython messing with the output
    # typical error: Unable to configure handler 'console': IOStream has no fileno
    # try without console output:
    print('WARNING: the colored console output is failing (possibly because of ipython). Switching to monochromatic '
          'output')
    _LOGCONFIG['handlers']['console']['class'] = "logging.StreamHandler"
    logging.config.dictConfig(_LOGCONFIG)

# Sets the __version__ variable
__version__ = __version__ + str(get_git_revision_tag())
