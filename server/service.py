import json
import os

import requests

from exception import JudgeServiceError
from utils import server_info, logger, token


class JudgeService(object):
    def heartbeat(self):
        try:
            resp = requests.post('http://localhost/ping',
                                 headers={"X-JUDGE-SERVER-TOKEN": token,
                                          "Content-Type": "application/json"}, timeout=5)
            if resp.status_code == 200:
                return 0
            return 1
        except Exception as e:
            logger.exception(e)
            raise JudgeServiceError("Heartbeat request failed")


if __name__ == "__main__":
    try:
        if not os.environ.get("DISABLE_HEARTBEAT"):
            service = JudgeService()
            exit(service.heartbeat())
        exit(0)
    except Exception as e:
        logger.exception(e)
        exit(1)
