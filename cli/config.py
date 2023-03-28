from platformdirs import PlatformDirs

from .model import Serialize, Account, Printer, Config

from pathlib import Path
import contextlib
import json

class BaseConfigManager:

    def __init__(self, dirs: PlatformDirs, classes=None):
        self._dirs = dirs
        if classes:
            self._classes = {t.__name__: t for t in classes}
        else:
            self._classes = []
        dirs.user_config_path.mkdir(exist_ok=True, parents=True)

    @contextlib.contextmanager
    def _borrow(self, value, write, default=None):
        if not default:
            default = {}
        pr = self.load(value, default)
        yield pr
        if write:
            self.save(value, pr)

    @property
    def config_root(self):
        return self._dirs.user_config_path

    def config_path(self, name):
        return self.config_root / Path(f"{name}.json")

    def _load_json(self, val):
        if "__type__" not in val:
            return val

        typename = val["__type__"]
        if typename not in self._classes:
            return val

        return self._classes[typename].from_dict(val)

    @staticmethod
    def _save_json(val):
        if not isinstance(val, Serialize):
            return val

        data = val.to_dict()
        data["__type__"] = type(val).__name__
        return data

    def load(self, name, default):
        path = self.config_path(name)
        if not path.exists():
            return default

        return json.load(path.open(), object_hook=self._load_json)

    def save(self, name, value):
        path = self.config_path(name)
        path.write_text(json.dumps(value, default=self._save_json, indent=2) + "\n")

class AnkerConfigManager(BaseConfigManager):

    def modify(self):
        return self._borrow("default", write=True)

    def open(self):
        return self._borrow("default", write=False)

def configmgr(profile="default"):
    return AnkerConfigManager(PlatformDirs("ankerctl"), classes=(Config, Account, Printer))
