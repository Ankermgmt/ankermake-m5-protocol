class GCodeMeta:

    def detect(self, fd):
        fd.seek(0)
        first_line = fd.read(1024).splitlines()[0]
        return self.detect_first_line(first_line)

    def detect_first_line(self, line):
        raise NotImplemented

    def load_props(self, fd):
        raise NotImplemented
