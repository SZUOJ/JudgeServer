import json
import os

import requests

from exception import JudgeServiceError
from utils import server_info, logger, token


class JudgeService:
    def __init__(self):
        self.service_url = os.environ["SERVICE_URL"]
        self.backend_url = os.environ["BACKEND_URL"]

    def _request(self, url, data=None):
        if data is None:
            data = {}
        try:
            return requests.post(url,
                                 json=data,
                                 headers={"X-JUDGE-SERVER-TOKEN": token,
                                          "Content-Type": "application/json"}, timeout=5)
        except Exception as exc:
            logger.exception(exc)
            raise JudgeServiceError("Heartbeat request failed")

    def heartbeat(self):
        try:
            info = self._request(url="http://localhost:8080/ping").json()["data"]
            info["action"] = "heartbeat"
            info["service_url"] = self.service_url
            try:
                self._request(url=self.backend_url, data=info)
            except Exception as exc:
                logger.exception(exc)
            return 0
        except Exception as e:
            return 1


if __name__ == "__main__":
    try:
        if not os.environ.get("DISABLE_HEARTBEAT"):
            service = JudgeService()
            exit(service.heartbeat())
        exit(0)
    except Exception as e:
        logger.exception(e)
        exit(1)
