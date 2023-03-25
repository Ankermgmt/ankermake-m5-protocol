import socket
import logging as log

from libflagship.pppp import *
from libflagship.util import enhex

# FILE_RECV_IDLE	0x0
# FILE_RECV_START	0x1
# FILE_RECV_BUSY	0x2
# FILE_RECV_DONE	0x3
# FILE_RECV_ERROR	0x4
# FILE_RECV_ABORT	0x5

LAN_SEARCH_PORT = 32108

class AnkerPPPPApi:

    def __init__(self, sock, drw_delay=0.10, addr=None):
        self.sock = sock
        self.ctr = [0] * 8
        self._drw_delay = drw_delay
        self.addr = addr

    @classmethod
    def open_broadcast(cls, timeout=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if timeout:
            sock.settimeout(timeout)
        addr = ("255.255.255.255", libflagship.pppapi.LAN_SEARCH_PORT)
        return cls(sock, addr=addr)

    def recv(self):
        data, self.addr = self.sock.recvfrom(4096)
        log.info(f"RX {enhex(data)} [{self.addr}]")
        msg = Message.parse(data)[0]
        log.debug(f"   {msg}")
        return msg

    def send(self, pkt, addr=None):
        resp = pkt.pack()
        log.info(f"TX {enhex(resp)}")
        msg = Message.parse(resp)[0]
        log.debug(f"   {msg}")
        self.sock.sendto(resp, addr or self.addr)

    def req(self, pkt, addr=None):
        log.debug("Request:")
        self.send(pkt, addr)
        return self.recv()

    def send_drw(self, chan, data):
        self.send(PktDrw(chan=chan, index=self.ctr[chan], data=data))
        self.ctr[chan] += 1
        time.sleep(self._drw_delay)

    def send_xzyh(self, data, cmd, unk0=0, unk1=0, unk2=0, unk3=0, dev_type=0):
        xzyh = Xzyh(
            cmd=cmd,
            len=len(data),
            data=data,
            chan=0,
            unk0=unk0,
            unk1=unk1,
            unk2=unk2,
            unk3=unk3,
            dev_type=dev_type
        )

        self.send_drw(chan=0, data=xzyh)

    def send_aabb(self, data, unk=0, cmd=0):
        header = Aabb(unk=unk, cmd=cmd, len=len(data)).pack()
        payload = header + data + ppcs_crc16(header[2:] + data)

        pdata = payload[:]
        while pdata:
            data, pdata = pdata[:1024], pdata[1024:]
            self.send_drw(chan=1, data=data)
