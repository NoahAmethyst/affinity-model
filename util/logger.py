import datetime
import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import coloredlogs
import http.client

from util.constant import AFFINITY_SERVER, AFFINITY_PORT
from util.time_util import now_millis

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(name='affinity-model')
coloredlogs.install(logger=logger)
logger.propagate = False


def init_logger():
    ## Setup logger color
    coloredFormatter = coloredlogs.ColoredFormatter(
        fmt='[%(name)s] %(asctime)s %(funcName)s %(lineno)-3d  %(message)s',
        level_styles=dict(
            debug=dict(color='white'),
            info=dict(color='green'),
            warning=dict(color='yellow', bright=True),
            error=dict(color='red', bold=True, bright=True),
            critical=dict(color='black', bold=True, background='red'),
        ),
        field_styles=dict(
            name=dict(color='white'),
            asctime=dict(color='white'),
            funcName=dict(color='white'),
            lineno=dict(color='white'),
        )
    )

    ## Setup logger streamHandler
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(fmt=coloredFormatter)
    logger.addHandler(hdlr=ch)
    logger.setLevel(level=logging.DEBUG)


