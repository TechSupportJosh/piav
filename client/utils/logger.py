import logging
import requests

from inspect import getargspec

# https://stackoverflow.com/a/24683360from inspect import getargspec
class BraceMessage(object):
    def __init__(self, fmt, args, kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return str(self.fmt).format(*self.args, **self.kwargs)


class StyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger):
        self.logger = logger

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, log_kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(msg, args, kwargs), (), **log_kwargs)

    def process(self, msg, kwargs):
        return msg, {
            key: kwargs[key]
            for key in getargspec(self.logger._log).args[1:]
            if key in kwargs
        }


class JSONHTTPHandler(logging.Handler):
    def __init__(self, host, endpoint):
        super(JSONHTTPHandler, self).__init__()

        self.host = host
        self.endpoint = endpoint

    def emit(self, record):
        print(record)
        requests.post(
            self.host + self.endpoint,
            json={"message": record.getMessage(), "levelno": record.levelno},
        )


def get_logger(API_URL, task_id):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("logger")

    http_handler = JSONHTTPHandler(API_URL, "/vm/log/" + task_id)
    http_handler.setLevel(logging.DEBUG)

    logger.addHandler(http_handler)

    return StyleAdapter(logger)
