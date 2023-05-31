class GCodeMeta:

    def detect(self, fd):
        fd.seek(0)
        first_line = fd.read(1024).splitlines()[0]
        return self.detect_first_line(first_line)

    def detect_first_line(self, line):
        raise NotImplemented

    def load_props(self, fd):
        raise NotImplemented


class GCodeMetaAuto(GCodeMeta):

    def __init__(self, types):
        self.types = types

    def detect(self, fd):
        for t in self.types:
            if res := t.detect(fd):
                self.type = t
                return res

    def detect_first_line(self, line):
        for t in self.types:
            if res := t.detect(fd):
                self.type = t
                return res

    def load_props(self, fd):
        return self.type.load_props(fd)
