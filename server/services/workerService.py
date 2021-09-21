import json

import requests

from server import config
from server.models import MetaData
from server.logger import logger

log = logger.get_logger('server')


def mco_api(meta_data: MetaData):
    data = {
        'x': meta_data.get_matrix_x(),
        'y': meta_data.get_matrix_y(),
        'freeChlen': meta_data.freeChlen,
        'h1': meta_data.get_row(meta_data.index_h1),
        'h2': meta_data.get_row(meta_data.index_h2)
    }

    try:
        url = config.URL_WORKER + 'mco'
        response = requests.post(url, json=data)

        if response.status_code >= 400:
            log.error('Exception request to worker: {0}'
                      .format(response.content.decode('utf-8')))
        else:
            return json.loads(response.content.decode('utf-8'))
    except Exception as e:
        log.error('Exception request to worker: {}'.format(e), exc_info=True,
                  stack_info=True)
