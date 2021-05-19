import logging

from colorama import init as colorama_init, Fore

colorama_init()


# Don't display /log POST requests, since their content is forwarded to our console anyways
class LogEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/log") == -1


class CustomFormatter(logging.Formatter):
    format_prefix = (
        Fore.RESET + "[%(asctime)s] <" + Fore.CYAN + "%(name)s" + Fore.RESET + "> "
    )
    format_suffix = "%(message)s " + Fore.RESET + "(%(filename)s:%(lineno)d)"

    colours = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED,
    }

    def format(self, record):
        return logging.Formatter(
            self.format_prefix + self.colours.get(record.levelno) + self.format_suffix,
            datefmt="%H:%M:%S",
        ).format(record)


class ClientFormatter(CustomFormatter):
    format_prefix = (
        Fore.RESET
        + "[%(asctime)s] <"
        + Fore.CYAN
        + "%(name)s"
        + Fore.RESET
        + ":"
        + Fore.RED
        + "%(task_id)s"
        + Fore.RESET
        + "> "
    )
    format_suffix = "%(message)s" + Fore.RESET
