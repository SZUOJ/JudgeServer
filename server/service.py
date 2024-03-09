import os

import requests

from utils import logger, token


class JudgeService:
    def __init__(self):
        self.service_url = os.environ["SERVICE_URL"]
        self.backend_url = os.environ["BACKEND_URL"]

    def _request(self, url, data=None):
        if data is None:
            data = {}
        return requests.post(
            url,
            json=data,
            headers={"X-JUDGE-SERVER-TOKEN": token, "Content-Type": "application/json"},
            timeout=5,
        )

    def heartbeat(self):
        try:
            self._request(url="http://localhost:8080/ping")
            return 0
        except Exception as e:
            logger.exception(f"Heartbeat request failed: {e}")
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
