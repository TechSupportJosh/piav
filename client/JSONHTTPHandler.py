import logging
import requests

class JSONHTTPHandler(logging.Handler):
    def __init__(self, host, endpoint):
        super(JSONHTTPHandler, self).__init__()

        self.host = host
        self.endpoint = endpoint

    def emit(self, record):
        print(record)
        requests.post(self.host + self.endpoint, json={
            "message": record.getMessage(),
            "levelno": record.levelno
        })
