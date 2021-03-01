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
            resp = requests.post(url, json=data,
                                 headers={"X-JUDGE-SERVER-TOKEN": token,
                                          "Content-Type": "application/json"}, timeout=5).text
        except Exception as exc:
            logger.exception(exc)
            raise JudgeServiceError("Heartbeat request failed")
        try:
            r = json.loads(resp)
            if r["error"]:
                raise JudgeServiceError(r["data"])
        except Exception as exc:
            logger.exception("Heartbeat failed, response is {}".format(resp))
            raise JudgeServiceError("Invalid heartbeat response")

    def heartbeat(self):
        self.heartbeat_backend()
        try:
            self._request(url='http://localhost:8080/ping')
            return 0
        except Exception as e:
            return 1

    def heartbeat_backend(self):
        """发送心跳包到后端"""
        data = server_info()
        data["action"] = "heartbeat"
        data["service_url"] = self.service_url
        try:
            self._request(url=self.backend_url, data=data)
        except Exception as exc:
            logger.exception(exc)


if __name__ == "__main__":
    try:
        if not os.environ.get("DISABLE_HEARTBEAT"):
            service = JudgeService()
            exit(service.heartbeat())
        exit(0)
    except Exception as e:
        logger.exception(e)
        exit(1)
