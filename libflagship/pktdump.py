from datetime import datetime
from .util import enhex


class PacketWriter:

    def __init__(self, fd):
        self.fd = fd

    @staticmethod
    def timestamp():
        return datetime.now().isoformat()

    @classmethod
    def open(cls, filename, append=True):
        fd = open(filename, "a" if append else "w")
        fd.write(f"# ========== {cls.timestamp()} Logging starts ==========\n")
        return cls(fd)

    def write(self, data, addr, type="-"):
        self.fd.write(f"{self.timestamp()} {type} {addr[0]}:{addr[1]} {enhex(data)}\n")

    def rx(self, data, addr):
        self.write(data, addr, type="RX")

    def tx(self, data, addr):
        self.write(data, addr, type="TX")
