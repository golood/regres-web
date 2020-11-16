import logging
import logging.config
from os import path

import yaml

from server.config import SPACE


def get_logger(name):
    with open(path.join(path.dirname(path.abspath(__file__)), 'config.yaml'), 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    if SPACE == 'dev':
        return logging.getLogger(name + 'Dev')
    else:
        return logging.getLogger(name)
