import os
import socket
import string
import hashlib
import logging as log

from enum import Enum
from multiprocessing import Pipe
from datetime import datetime, timedelta
from threading import Thread, Event, Lock
from socket import AF_INET
from dataclasses import dataclass

from libflagship.cyclic import CyclicU16
from libflagship.pppp import Type, \
    PktDrw, PktDrwAck, PktClose, PktSessionReady, PktAliveAck, PktDevLgnAckCrc, \
    PktHelloAck, PktP2pRdyAck, PktP2pRdy, PktLanSearch, \
    Host, Message, Xzyh, Aabb, FileTransferReply


PPPP_LAN_PORT = 32108
PPPP_WAN_PORT = 32100


class PPPPError(Exception):

    def __init__(self, err, message):
        self.err = err
        super().__init__(message)


@dataclass
class FileUploadInfo:
    name: str
    size: str
    md5: str
    user_name: str
    user_id: str
    machine_id: str
    type: int = 0

    @staticmethod
    def sanitize_filename(str):
        whitelist = string.ascii_letters + string.digits + "._-"

        def sanitize(c):
            if c in whitelist:
                return c
            else:
                return "_"

        cleaned = "".join(sanitize(c) for c in str)
        return cleaned.lstrip(".").replace("..", ".")

    @classmethod
    def from_file(cls, filename, user_name, user_id, machine_id, type=0):
        data = open(filename, "rb").read()
        return cls.from_data(data, filename, user_name, user_id, machine_id, type=0)

    @classmethod
    def from_data(cls, data, filename, user_name, user_id, machine_id, type=0):
        return cls(
            name=cls.sanitize_filename(os.path.basename(filename)),
            size=len(data),
            md5=hashlib.md5(data).hexdigest(),
            user_name=user_name,
            user_id=user_id,
            machine_id=machine_id,
            type=type
        )

    def __str__(self):
        return f"{self.type},{self.name},{self.size},{self.md5},{self.user_name},{self.user_id},{self.machine_id}"

    def __bytes__(self):
        return str(self).encode() + b"\x00"


class Wire:

    def __init__(self):
        self.buf = []
        self.rx, self.tx = Pipe(False)

    def peek(self, size, timeout=None):
        # Zero timeout on self.rx.poll() means "wait forever", but we want it to
        # mean "no wait", so we emulate that by setting it to 1us.
        if timeout == 0.0:
            timeout = 0.000001

        if timeout is not None:
            deadline = datetime.now() + timedelta(seconds=timeout)

        while len(self.buf) < size:
            if timeout and not self.rx.poll(timeout=(deadline - datetime.now()).total_seconds()):
                return None
            self.buf.extend(self.rx.recv())

        return bytes(self.buf[:size])

    def read(self, size, timeout=None):
        res = self.peek(size, timeout)
        if res:
            self.buf = self.buf[size:]
        return res

    def write(self, data):
        self.tx.send(data)


class Channel:

    def __init__(self, index, max_in_flight=64, max_age_warn=128):
        self.index = index
        self.rxqueue = {}
        self.txqueue = []
        self.backlog = []
        self.rx_ctr = CyclicU16(0)
        self.tx_ctr = CyclicU16(0)
        self.tx_ack = CyclicU16(0)
        self.rx = Wire()
        self.tx = Wire()
        self.timeout = timedelta(seconds=0.5)
        self.acks = set()
        self.event = Event()
        self.max_in_flight = max_in_flight
        self.max_age_warn = max_age_warn
        self.lock = Lock()

    def rx_ack(self, acks):
        # remove all ACKed packets from transmission queue
        self.txqueue = [tx for tx in self.txqueue if tx[1] not in acks]

        # record any ACKs that are not yet confirmed
        for ack in acks:
            if ack >= self.tx_ack:
                self.acks.add(ack)

        # update tx_ack step by step
        while self.tx_ack in self.acks:
            self.acks.remove(self.tx_ack)
            self.tx_ack += 1

    def rx_drw(self, index, data):
        # drop any packets we have already recieved
        if self.rx_ctr > index:
            if self.max_age_warn and (self.rx_ctr - index > self.max_age_warn):
                log.warn(f"Dropping old packet: index {index} while expecting {self.rx_ctr}.")
            return

        # record packet in queue
        self.rxqueue[index] = data

        # recombine data from queue
        while self.rx_ctr in self.rxqueue:
            data = self.rxqueue[self.rx_ctr]
            del self.rxqueue[self.rx_ctr]
            self.rx_ctr += 1
            self.rx.write(data)

    def poll(self):
        # signal event to make blocking reads check status again
        self.event.set()

        txq = self.txqueue

        if self.backlog and len(txq) < self.max_in_flight:
            while self.backlog and len(txq) < self.max_in_flight:
                txq.append(self.backlog.pop(0))

            # sort list to make sure oldest deadline is first
            txq.sort()

        res = []
        now = datetime.now()

        while txq and txq[0][0] < now:
            deadline, index, pkt = txq.pop(0)
            res.append(PktDrw(chan=self.index, index=index, data=pkt))
            txq.append((deadline + self.timeout, index, pkt))

        # the returned chunks will be (re)transmitted
        return res

    def wait(self):
        self.event.wait()
        self.event.clear()

    def peek(self, nbytes, timeout=None):
        return self.rx.peek(nbytes, timeout)

    def read(self, nbytes, timeout=None):
        return self.rx.read(nbytes, timeout)

    def write(self, payload, block=True):
        pdata = payload[:]

        tx_ctr_start = self.tx_ctr

        # schedule all packets, starting from current time
        deadline = datetime.now()
        while pdata:
            # schedule transmission in 1kb chunks
            data, pdata = pdata[:1024], pdata[1024:]
            self.backlog.append((deadline, self.tx_ctr, data))
            self.tx_ctr += 1

        tx_ctr_done = self.tx_ctr

        while block:
            # if doing a blocking write, loop on self.event until we have
            # received acknowledgment of our data
            self.wait()

            if self.tx_ack >= tx_ctr_done:
                break

        return (tx_ctr_start, tx_ctr_done)


class PPPPState(Enum):
    Idle         = 1
    Connecting   = 2
    Connected    = 3
    Disconnected = 4


class AnkerPPPPBaseApi(Thread):

    def __init__(self, sock, duid, addr=None):
        super().__init__()
        self.sock = sock
        self.duid = duid
        self.addr = addr

        self.state = PPPPState.Idle
        self.chans = [Channel(n) for n in range(8)]

        self.running = True
        self.stopped = Event()
        self.dumper = None

    @classmethod
    def open(cls, duid, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return cls(sock, duid, addr=(host, port))

    @classmethod
    def open_lan(cls, duid, host):
        return cls.open(duid, host, PPPP_LAN_PORT)

    @classmethod
    def open_wan(cls, duid, host):
        return cls.open(duid, host, PPPP_WAN_PORT)

    @classmethod
    def open_broadcast(cls, bind_addr=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if bind_addr is not None:
            sock.bind((bind_addr, 0))
        addr = ("255.255.255.255", PPPP_LAN_PORT)
        return cls(sock, duid=None, addr=addr)

    def connect_lan_search(self):
        self.state = PPPPState.Connecting
        self.send(PktLanSearch())

    def set_dumper(self, dumper):
        self.dumper = dumper

    def stop(self):
        self.running = False
        self.stopped.wait()

    def run(self):
        log.debug("Started pppp thread")
        while self.running:
            try:
                msg = self.recv(timeout=0.05)
                self.process(msg)
            except TimeoutError:
                pass
            except ConnectionResetError:
                break

            for idx, ch in enumerate(self.chans):
                for pkt in ch.poll():
                    self.send(pkt)

        self.send(PktClose())

        self.stopped.set()

    @property
    def host(self):
        return Host(afam=AF_INET, addr=self.addr[0], port=self.addr[1])

    def process(self, msg):

        if msg.type == Type.CLOSE:
            log.error("CLOSE")
            raise ConnectionResetError

        elif msg.type == Type.REPORT_SESSION_READY:
            pkt = PktSessionReady(
                duid=self.duid,
                handle=-3,
                max_handles=5,
                active_handles=1,
                startup_ticks=0,
                b1=1, b2=0, b3=1, b4=0,
                addr_local=Host(afam=AF_INET, addr="0.0.0.0", port=0),
                addr_wan=Host(afam=AF_INET, addr="0.0.0.0", port=0),
                addr_relay=Host(afam=AF_INET, addr="0.0.0.0", port=0)
            )

            # self.send(pkt)

        elif msg.type == Type.ALIVE:
            self.send(PktAliveAck())

        elif msg.type == Type.DRW:
            self.send(PktDrwAck(chan=msg.chan, count=1, acks=[msg.index]))
            self.chans[msg.chan].rx_drw(msg.index, msg.data)

        elif msg.type == Type.DRW_ACK:
            self.chans[msg.chan].rx_ack(msg.acks)

        elif msg.type == Type.DEV_LGN_CRC:
            self.send(PktDevLgnAckCrc())

        elif msg.type == Type.HELLO:
            self.send(PktHelloAck(host=self.host))

        elif msg.type == Type.ALIVE_ACK:
            pass

        elif msg.type == Type.P2P_RDY:
            self.send(PktP2pRdyAck(duid=self.duid, host=self.host))
            self.state = PPPPState.Connected

        elif msg.type == Type.PUNCH_PKT:
            if self.state == PPPPState.Connecting:
                self.send(PktClose())
                self.send(PktP2pRdy(self.duid))

    def recv(self, timeout=None):
        if self.state in {PPPPState.Idle, PPPPState.Disconnected}:
            raise ConnectionError(f"Tried to recv packet in state {self.state}")

        self.sock.settimeout(timeout)
        data, self.addr = self.sock.recvfrom(4096)
        if self.dumper:
            self.dumper.rx(data, self.addr)
        msg = Message.parse(data)[0]
        log.debug(f"RX <--  {str(msg)[:128]}")
        return msg

    def send(self, pkt, addr=None):
        if self.state in {PPPPState.Idle, PPPPState.Disconnected}:
            raise ConnectionError(f"Tried to send packet in state {self.state}")

        resp = pkt.pack()
        if self.dumper:
            self.dumper.tx(resp, self.addr)
        msg = Message.parse(resp)[0]
        log.debug(f"TX  --> {str(msg)[:128]}")
        self.sock.sendto(resp, addr or self.addr)

    def send_xzyh(self, data, cmd, chan=0, unk0=0, unk1=0, sign_code=0, unk3=0, dev_type=0, block=True):
        xzyh = Xzyh(
            cmd=cmd,
            len=len(data),
            data=data,
            chan=chan,
            unk0=unk0,
            unk1=unk1,
            sign_code=sign_code,
            unk3=unk3,
            dev_type=dev_type
        )

        return self.chans[chan].write(xzyh.pack(), block=block)

    def send_aabb(self, data, sn=0, pos=0, frametype=0, chan=1, block=True):
        aabb = Aabb(
            frametype=frametype,
            sn=sn,
            pos=pos,
            len=len(data)
        )

        return self.chans[chan].write(aabb.pack_with_crc(data), block=block)


class AnkerPPPPApi(AnkerPPPPBaseApi):

    def __init__(self, sock, duid, addr=None):
        super().__init__(sock, duid, addr)
        self.daemon = True

    def recv_xzyh(self, chan=1, timeout=None):
        fd = self.chans[chan]

        with fd.lock:
            hdr = fd.peek(16, timeout=timeout)
            if not hdr:
                return None

            xzyh = Xzyh.parse(hdr)[0]

            data = fd.read(xzyh.len + 16, timeout=timeout)
            if not data:
                return None

            xzyh.data = data[16:]
            return xzyh

    def recv_aabb(self, chan=1):
        fd = self.chans[chan]

        data = fd.read(12)
        aabb = Aabb.parse(data)[0]
        p = data + fd.read(aabb.len + 2)
        aabb, data = Aabb.parse_with_crc(p)[:2]
        return aabb, data

    def recv_aabb_reply(self, chan=1, check=True):
        aabb, data = self.recv_aabb(chan=chan)
        if len(data) != 1:
            raise ValueError(f"Unexpected reply from aabb request: {data}")

        res = FileTransferReply(data[0])
        if check and res != FileTransferReply.OK:
            raise PPPPError(res, f"Aabb request failed: {res.name}")

        return res

    def aabb_request(self, data, frametype, pos=0, chan=1, check=True):
        self.send_aabb(data=data, frametype=frametype, chan=chan, pos=pos)
        return self.recv_aabb_reply(chan, check)


class AnkerPPPPAsyncApi(AnkerPPPPBaseApi):

    def poll(self, timeout=None):
        msg = None
        try:
            msg = self.recv(timeout=timeout)
            self.process(msg)
        except TimeoutError:
            pass

        for idx, ch in enumerate(self.chans):
            for pkt in ch.poll():
                self.send(pkt)

        return msg
