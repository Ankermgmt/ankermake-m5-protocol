import json


class JsonDatabase:

    def __init__(self, filename, initial_contents=None):
        self.filename = filename
        self.db = initial_contents or {}

    def load(self):
        self.db = json.load(open(self.filename))

    def save(self, fd):
        fd.write(json.dumps(self.db, indent=4, sort_keys=True))

    def sync(self):
        with open(self.filename, "w") as fd:
            self.save(fd)

    def get(self, key):
        d = self.db
        parts = key.split(".")
        for k in parts:
            if k not in d:
                return None
            d = d[k]

        return d

    def set(self, key, value):
        d = self.db
        parts = key.split(".")
        for k in parts[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[parts[-1]] = value
        self.sync()

    def delete(self, key):
        d = self.db
        parts = key.split(".")
        for k in parts[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        if parts[-1] in d:
            del d[parts[-1]]
        self.sync()
