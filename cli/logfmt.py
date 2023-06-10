import click
import logging


class ColorFormatter(logging.Formatter):

    def __init__(self, fmt):
        super().__init__(fmt)

        self._colors = {
            logging.CRITICAL: "red",
            logging.ERROR:    "red",
            logging.WARNING:  "yellow",
            logging.INFO:     "green",
            logging.DEBUG:    "magenta",
        }

        self._marks = {
            logging.CRITICAL: "!",
            logging.ERROR:    "E",
            logging.WARNING:  "W",
            logging.INFO:     "*",
            logging.DEBUG:    "D",
        }

    default_msec_format = click.style("%s.%03d", dim=True)

    def format(self, rec):
        marks, colors = self._marks, self._colors
        return "".join([
            click.style("[",                fg="blue",              bold=True),
            click.style(marks[rec.levelno], fg=colors[rec.levelno], bold=True),
            click.style("]",                fg="blue",              bold=True),
            " ",
            super().format(rec),
        ])


class ExitOnExceptionHandler(logging.StreamHandler):

    def emit(self, record):
        super().emit(record)
        if record.levelno == logging.CRITICAL:
            raise SystemExit(127)


def setup_logging(level=logging.INFO):
    logging.basicConfig(handlers=[ExitOnExceptionHandler()])
    log = logging.getLogger()
    log.setLevel(level)
    handler = log.handlers[0]
    handler.setFormatter(ColorFormatter("[%(asctime)s] %(message)s"))
    return log
