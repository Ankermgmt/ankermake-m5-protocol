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


class ExitOnExceptionHandler(logging.StreamHandler):

    def emit(self, record):
        super().emit(record)
        if record.levelno == logging.CRITICAL:
            raise SystemExit(127)


def setup_logging(level=logging.INFO, log_dir=None):
    handlers = [ExitOnExceptionHandler()]
    
    if log_dir:
        import os
        os.makedirs(log_dir, exist_ok=True)
        
        # Root logger file handler (everything)
        root_handler = logging.FileHandler(os.path.join(log_dir, "ankerctl.log"))
        root_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        handlers.append(root_handler)
        
        # Specific file handlers for named loggers
        loggers = {
            "mqtt": "mqtt.log",
            "web": "web.log",
            "history": "history.log",
            "timelapse": "timelapse.log",
            "homeassistant": "homeassistant.log",
        }
        
        for name, filename in loggers.items():
            logger = logging.getLogger(name)
            handler = logging.FileHandler(os.path.join(log_dir, filename))
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
            logger.addHandler(handler)
            # We keep propagate=True so logs also go to root handler (stdout + ankerctl.log)

    logging.basicConfig(handlers=handlers, level=level)
    
    # Configure root logger formatter for stdout
    log = logging.getLogger()
    # basicConfig only adds handler if none exist, but we passed handlers explicitly.
    # The first handler in our list is ExitOnExceptionHandler (StreamHandler).
    # We need to set its formatter.
    for h in log.handlers:
        if isinstance(h, ExitOnExceptionHandler):
            h.setFormatter(ColorFormatter("%(message)s"))
            
    return log

