from platformdirs import PlatformDirs

from pathlib import Path
import contextlib
import json

class BaseConfigManager:

    def __init__(self, dirs: PlatformDirs):
        self._dirs = dirs
        dirs.user_config_path.mkdir(exist_ok=True)

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

    def load(self, name, default):
        path = self.config_path(name)
        if not path.exists():
            return default

        return json.load(path.open())

    def save(self, name, value):
        path = self.config_path(name)
        path.write_text(json.dumps(value))

class AnkerConfigManager(BaseConfigManager):

    def printers(self, write=False):
        return self._borrow("printers", [], write)

def configmgr():
    return AnkerConfigManager(PlatformDirs("ankerctl"))
