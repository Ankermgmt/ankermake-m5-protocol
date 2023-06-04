import shlex


class GCode:

    def __init__(self, code):
        self.raw = code

        words = shlex.split(code)
        self.cmd = words[0]
        self.args = words[1:]
        self.vals = {}

        for arg in self.args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                self.vals[k] = v

    def __str__(self):
        return self.raw

    def __repr__(self):
        return f"GCode<{self.raw!r}>"
