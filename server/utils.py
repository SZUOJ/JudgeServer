import hashlib
import logging.handlers
import os
import socket

import judger
import psutil

from config import DEBUG, SERVER_LOG_PATH
from exception import JudgeClientError

logger = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler(SERVER_LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


def server_info():
    ver = judger.VERSION
    return {"hostname": socket.gethostname(),
            "cpu": psutil.cpu_percent(),
            "cpu_core": psutil.cpu_count(),
            "memory": psutil.virtual_memory().percent,
            "judger_version": ".".join([str((ver >> 16) & 0xff), str((ver >> 8) & 0xff), str(ver & 0xff)])}


def get_token():
    token = os.environ.get("TOKEN")
    if not token:
        raise JudgeClientError("env 'TOKEN' not found")
    return token


class ProblemIOMode:
    standard = "stdio"
    file = "file"


token = hashlib.sha256(get_token().encode("utf-8")).hexdigest()
