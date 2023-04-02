import socket
import logging as log

from multiprocessing import Pipe, connection
from datetime import datetime, timedelta
from threading import Event

from libflagship.pppp import *
from libflagship.util import enhex

LAN_SEARCH_PORT = 32108


class FileUploadInfo:

    def __init__(self, name, size, md5, user_name, user_id, machine_id, type=0):
        self.name = name
        self.size = size
        self.md5 = md5
        self.user_name = user_name
        self.user_id = user_id
        self.machine_id = machine_id
        self.type = type

    def __str__(self):
        return f"{self.type},{self.name},{self.size},{self.md5},{self.user_name},{self.user_id},{self.machine_id}"


class Wire:

    def __init__(self):
        self.buf = []
        self.rx, self.tx = Pipe(False)

    def read(self, size):
        while len(self.buf) < size:
            self.buf.extend(self.rx.recv())
        res, self.buf = self.buf[:size], self.buf[size:]
        return bytes(res)

    def write(self, data):
        self.tx.send(data)


class Channel:

    def __init__(self, index):
        self.index = index
        self.rxqueue = {}
        self.txqueue = []
        self.rx_ctr = 0
        self.tx_ctr = 0
        self.tx_ack = 0
        self.rx = Wire()
        self.tx = Wire()
        self.timeout = timedelta(seconds=0.5)
        self.acks = set()
        self.event = Event()

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
            if self.rx_ctr - index > 20:
                log.warn(f"Dropping old packet: index {index} while expecting {self.rx_ctr}.")
            return

        # record packet in queue
        self.rxqueue[index] = data

        # recombine data from queue
        while self.rx_ctr in self.rxqueue:
            del self.rxqueue[self.rx_ctr]
            self.rx_ctr = (self.rx_ctr + 1) & 0xFFFF
            self.rx.write(data)

    def poll(self):
        # signal event to make blocking reads check status again
        self.event.set()

        txq = self.txqueue

        res = []
        now = datetime.now()

        while txq and txq[0][0] < now:
            pkt = txq.pop(0)
            res.append(PktDrw(chan=self.index, index=pkt[1], data=pkt[2]))
            txq.append((pkt[0] + self.timeout, pkt[1], pkt[2]))

        # the returned chunks will be (re)transmitted
        return res

    def read(self, nbytes):
        return self.rx.read(nbytes)

    def write(self, payload, block=True):
        pdata = payload[:]

        # schedule all packets, starting from current time
        deadline = datetime.now()
        while pdata:
            # schedule transmission in 1kb chunks
            data, pdata = pdata[:1024], pdata[1024:]
            self.txqueue.append((deadline, self.tx_ctr, data))
            self.tx_ctr = (self.tx_ctr + 1) & 0xFFFF

            # schedule packets slightly apart, to avoid huge packet bursts
            deadline += timedelta(seconds=0.001)

        tx_ctr_done = self.tx_ctr

        while block:
            # if doing a blocking write, loop on self.event until we have
            # received acknowledgment of our data
            self.event.wait()
            self.event.clear()

            if self.tx_ack >= tx_ctr_done:
                break


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
        addr = ("255.255.255.255", LAN_SEARCH_PORT)
        return cls(sock, addr=addr)

    def recv(self):
        data, self.addr = self.sock.recvfrom(4096)
        log.debug(f"RX {enhex(data)} [{self.addr}]")
        msg = Message.parse(data)[0]
        log.debug(f"RX {msg}")
        return msg

    def send(self, pkt, addr=None):
        resp = pkt.pack()
        log.debug(f"TX {enhex(resp)}")
        msg = Message.parse(resp)[0]
        log.debug(f"TX {msg}")
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
