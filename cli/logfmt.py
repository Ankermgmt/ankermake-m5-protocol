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

    def format(self, rec):
        marks, colors = self._marks, self._colors
        return "".join([
            click.style("[",                fg="blue",              bold=True),
            click.style(marks[rec.levelno], fg=colors[rec.levelno], bold=True),
            click.style("]",                fg="blue",              bold=True),
            " ",
            super().format(rec),
        ])

def setup_logging():
    log = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    ch.setFormatter(ColorFormatter("%(message)s"))
    log.addHandler(ch)
    return log
