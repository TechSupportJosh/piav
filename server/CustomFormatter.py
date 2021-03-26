import logging

from colorama import init as colorama_init, Fore
colorama_init()


class CustomFormatter(logging.Formatter):
    format_prefix = "[%(asctime)s] <" + Fore.CYAN + "%(module)s" + Fore.RESET + ">: "
    format_suffix = "%(message)s (%(filename)s:%(lineno)d)"

    colours = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED
    }

    def format(self, record):
        return logging.Formatter(self.format_prefix + self.colours.get(record.levelno) + self.format_suffix).format(record)