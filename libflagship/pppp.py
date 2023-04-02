## ------------------------------------------
## Generated by Transwarp
##
## THIS FILE IS AUTOMATICALLY GENERATED.
## DO NOT EDIT. ALL CHANGES WILL BE LOST.
## ------------------------------------------

import struct
import enum
from dataclasses import dataclass, field
from .amtypes import *
from .amtypes import _assert_equal
from .megajank import crypto_curse_string, crypto_decurse_string, simple_encrypt_string, simple_decrypt_string
from .util import ppcs_crc16

class Type(enum.IntEnum):
    HELLO                     = 0x00 # unknown
    HELLO_ACK                 = 0x01 # unknown
    HELLO_TO                  = 0x02 # unknown
    HELLO_TO_ACK              = 0x03 # unknown
    QUERY_DID                 = 0x08 # unknown
    QUERY_DID_ACK             = 0x09 # unknown
    DEV_LGN                   = 0x10 # unknown
    DEV_LGN_ACK               = 0x11 # unknown
    DEV_LGN_CRC               = 0x12 # unknown
    DEV_LGN_ACK_CRC           = 0x13 # unknown
    DEV_LGN_KEY               = 0x14 # unknown
    DEV_LGN_ACK_KEY           = 0x15 # unknown
    DEV_LGN_DSK               = 0x16 # unknown
    DEV_ONLINE_REQ            = 0x18 # unknown
    DEV_ONLINE_REQ_ACK        = 0x19 # unknown
    P2P_REQ                   = 0x20 # unknown
    P2P_REQ_ACK               = 0x21 # unknown
    P2P_REQ_DSK               = 0x26 # unknown
    LAN_SEARCH                = 0x30 # unknown
    LAN_NOTIFY                = 0x31 # unknown
    LAN_NOTIFY_ACK            = 0x32 # unknown
    PUNCH_TO                  = 0x40 # unknown
    PUNCH_PKT                 = 0x41 # unknown
    PUNCH_PKT_EX              = 0x41 # unknown
    P2P_RDY                   = 0x42 # unknown
    P2P_RDY_EX                = 0x42 # unknown
    P2P_RDY_ACK               = 0x43 # unknown
    RS_LGN                    = 0x60 # unknown
    RS_LGN_ACK                = 0x61 # unknown
    RS_LGN1                   = 0x62 # unknown
    RS_LGN1_ACK               = 0x63 # unknown
    LIST_REQ1                 = 0x67 # unknown
    LIST_REQ                  = 0x68 # unknown
    LIST_REQ_ACK              = 0x69 # unknown
    LIST_REQ_DSK              = 0x6a # unknown
    RLY_HELLO                 = 0x70 # unknown
    RLY_HELLO_ACK             = 0x71 # unknown
    RLY_PORT                  = 0x72 # unknown
    RLY_PORT_ACK              = 0x73 # unknown
    RLY_PORT_KEY              = 0x74 # unknown
    RLY_PORT_ACK_KEY          = 0x75 # unknown
    RLY_BYTE_COUNT            = 0x78 # unknown
    RLY_REQ                   = 0x80 # unknown
    RLY_REQ_ACK               = 0x81 # unknown
    RLY_TO                    = 0x82 # unknown
    RLY_PKT                   = 0x83 # unknown
    RLY_RDY                   = 0x84 # unknown
    RLY_TO_ACK                = 0x85 # unknown
    RLY_SERVER_REQ            = 0x87 # unknown
    RLY_SERVER_REQ_ACK        = 0x87 # unknown
    SDEV_RUN                  = 0x90 # unknown
    SDEV_LGN                  = 0x91 # unknown
    SDEV_LGN_ACK              = 0x91 # unknown
    SDEV_LGN_CRC              = 0x92 # unknown
    SDEV_LGN_ACK_CRC          = 0x92 # unknown
    SDEV_REPORT               = 0x94 # unknown
    CONNECT_REPORT            = 0xa0 # unknown
    REPORT_REQ                = 0xa1 # unknown
    REPORT                    = 0xa2 # unknown
    DRW                       = 0xd0 # unknown
    DRW_ACK                   = 0xd1 # unknown
    PSR                       = 0xd8 # unknown
    ALIVE                     = 0xe0 # unknown
    ALIVE_ACK                 = 0xe1 # unknown
    CLOSE                     = 0xf0 # unknown
    MGM_DUMP_LOGIN_DID        = 0xf4 # unknown
    MGM_DUMP_LOGIN_DID_DETAIL = 0xf5 # unknown
    MGM_DUMP_LOGIN_DID_1      = 0xf6 # unknown
    MGM_LOG_CONTROL           = 0xf7 # unknown
    MGM_REMOTE_MANAGEMENT     = 0xf8 # unknown
    REPORT_SESSION_READY      = 0xf9 # unknown
    INVALID                   = 0xff # unknown

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]

class P2PCmdType(enum.IntEnum):
    P2P_JSON_CMD  = 0x06a4 # unknown
    P2P_SEND_FILE = 0x3a98 # unknown

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]

class P2PSubCmdType(enum.IntEnum):
    START_LIVE          = 0x03e8 # unknown
    CLOSE_LIVE          = 0x03e9 # unknown
    VIDEO_RECORD_SWITCH = 0x03ea # unknown
    LIGHT_STATE_SWITCH  = 0x03ab # unknown
    LIGHT_STATE_GET     = 0x03ec # unknown
    LIVE_MODE_SET       = 0x03ed # unknown
    LIVE_MODE_GET       = 0x03ee # unknown

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]

class FileTransfer(enum.IntEnum):
    BEGIN = 0x00 # Begin file transfer (sent with metadata)
    DATA  = 0x01 # File content
    END   = 0x02 # Complete file transfer (start printing)
    ABORT = 0x03 # Abort file transfer (delete file)

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]


@dataclass
class Message:

    type: Type = field(repr=False, init=False)

    @classmethod
    def parse(cls, m):
        magic, type, size = struct.unpack(">BBH", m[:4])
        assert magic == 0xF1
        type = Type(type)
        p = m[4:4+size]
        if type in MessageTypeTable:
            return MessageTypeTable[type].parse(p)
        else:
            raise ValueError(f"unknown message type {type:02x}")

    def pack(self, p):
        return struct.pack(">BBH", 0xF1, self.type, len(p)) + p

class _Host:
    pass

class _Duid:
    def __str__(self):
        return f"{self.prefix}-{self.serial:06}-{self.check}"

class _Xzyh:
    pass

class _Aabb:

    @classmethod
    def parse_with_crc(cls, m):
        head, m = m[:12], m[12:]
        header = cls.parse(head)[0]
        data, m = m[:header.len], m[header.len:]
        crc1, m  = m[:2], m[2:]
        crc2 = ppcs_crc16(head[2:] + data)
        _assert_equal(crc1, crc2)
        return header, data, m

    def pack_with_crc(self, data):
        header = self.pack()

        return header + data + ppcs_crc16(header[2:] + data)

class _Dsk:
    pass

class _Version:
    pass

@dataclass
class Host(_Host):
    pad0 : bytes = field(repr=False, kw_only=True, default='\x00' * 1) # unknown
    afam : u8le # Adress family. Set to AF_INET (2)
    port : u16le # Port number
    addr : IPv4 # IP address
    pad1 : bytes = field(repr=False, kw_only=True, default='\x00' * 8) # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        pad0, p = Zeroes.parse(p, 1)
        afam, p = u8le.parse(p)
        port, p = u16le.parse(p)
        addr, p = IPv4.parse(p)
        pad1, p = Zeroes.parse(p, 8)

        return cls(pad0=pad0, afam=afam, port=port, addr=addr, pad1=pad1), p

    def pack(self):
        p  = Zeroes.pack(self.pad0, 1)
        p += u8le.pack(self.afam)
        p += u16le.pack(self.port)
        p += IPv4.pack(self.addr)
        p += Zeroes.pack(self.pad1, 8)

        # not encrypted
        return p

@dataclass
class Duid(_Duid):
    prefix : bytes # duid "prefix", 7 chars + NULL terminator
    serial : u32 # device serial number
    check  : bytes # checkcode relating to prefix+serial
    pad0   : bytes = field(repr=False, kw_only=True, default='\x00' * 2) # padding

    @classmethod
    def parse(cls, p):
        # not encrypted
        prefix, p = String.parse(p, 8)
        serial, p = u32.parse(p)
        check, p = String.parse(p, 6)
        pad0, p = Zeroes.parse(p, 2)

        return cls(prefix=prefix, serial=serial, check=check, pad0=pad0), p

    def pack(self):
        p  = String.pack(self.prefix, 8)
        p += u32.pack(self.serial)
        p += String.pack(self.check, 6)
        p += Zeroes.pack(self.pad0, 2)

        # not encrypted
        return p

@dataclass
class Xzyh(_Xzyh):
    magic     : bytes = field(repr=False, kw_only=True, default=b'XZYH') # unknown
    cmd       : u16le # unknown
    len       : u32le # unknown
    unk0      : u8 # unknown
    unk1      : u8 # unknown
    chan      : u8 # unknown
    sign_code : u8 # unknown
    unk3      : u8 # unknown
    dev_type  : u8 # unknown
    data      : bytes # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        magic, p = Magic.parse(p, 4, b'XZYH')
        cmd, p = u16le.parse(p)
        len, p = u32le.parse(p)
        unk0, p = u8.parse(p)
        unk1, p = u8.parse(p)
        chan, p = u8.parse(p)
        sign_code, p = u8.parse(p)
        unk3, p = u8.parse(p)
        dev_type, p = u8.parse(p)
        data, p = Bytes.parse(p, len)

        return cls(magic=magic, cmd=cmd, len=len, unk0=unk0, unk1=unk1, chan=chan, sign_code=sign_code, unk3=unk3, dev_type=dev_type, data=data), p

    def pack(self):
        p  = Magic.pack(self.magic, 4, b'XZYH')
        p += u16le.pack(self.cmd)
        p += u32le.pack(self.len)
        p += u8.pack(self.unk0)
        p += u8.pack(self.unk1)
        p += u8.pack(self.chan)
        p += u8.pack(self.sign_code)
        p += u8.pack(self.unk3)
        p += u8.pack(self.dev_type)
        p += Bytes.pack(self.data, self.len)

        # not encrypted
        return p

@dataclass
class Aabb(_Aabb):
    signature : bytes = field(repr=False, kw_only=True, default=b'\xaa\xbb') # Signature bytes. Must be 0xAABB
    flags     : u8 # Flags (unknown meaning, only seen as 0x80)
    sn        : u8 # Session id
    cmd       : u32le # Command field (P2PCmdType)
    len       : u32le # Length field

    @classmethod
    def parse(cls, p):
        # not encrypted
        signature, p = Magic.parse(p, 2, b'\xaa\xbb')
        flags, p = u8.parse(p)
        sn, p = u8.parse(p)
        cmd, p = u32le.parse(p)
        len, p = u32le.parse(p)

        return cls(signature=signature, flags=flags, sn=sn, cmd=cmd, len=len), p

    def pack(self):
        p  = Magic.pack(self.signature, 2, b'\xaa\xbb')
        p += u8.pack(self.flags)
        p += u8.pack(self.sn)
        p += u32le.pack(self.cmd)
        p += u32le.pack(self.len)

        # not encrypted
        return p

@dataclass
class Dsk(_Dsk):
    key : bytes # unknown
    pad : bytes = field(repr=False, kw_only=True, default='\x00' * 4) # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        key, p = Bytes.parse(p, 20)
        pad, p = Zeroes.parse(p, 4)

        return cls(key=key, pad=pad), p

    def pack(self):
        p  = Bytes.pack(self.key, 20)
        p += Zeroes.pack(self.pad, 4)

        # not encrypted
        return p

@dataclass
class Version(_Version):
    major : u8 # unknown
    minor : u8 # unknown
    patch : u8 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        major, p = u8.parse(p)
        minor, p = u8.parse(p)
        patch, p = u8.parse(p)

        return cls(major=major, minor=minor, patch=patch), p

    def pack(self):
        p  = u8.pack(self.major)
        p += u8.pack(self.minor)
        p += u8.pack(self.patch)

        # not encrypted
        return p


@dataclass
class PktDrw(Message):
    type = Type.DRW
    signature : bytes = field(repr=False, kw_only=True, default=b'\xd1') # Signature byte. Must be 0xD1
    chan      : u8 # Channel index
    index     : u16 # Packet index
    data      : bytes # Payload

    @classmethod
    def parse(cls, p):
        # not encrypted
        signature, p = Magic.parse(p, 1, b'\xd1')
        chan, p = u8.parse(p)
        index, p = u16.parse(p)
        data, p = Tail.parse(p)

        return cls(signature=signature, chan=chan, index=index, data=data), p

    def pack(self):
        p  = Magic.pack(self.signature, 1, b'\xd1')
        p += u8.pack(self.chan)
        p += u16.pack(self.index)
        p += Tail.pack(self.data)

        # not encrypted
        return super().pack(p)

@dataclass
class PktDrwAck(Message):
    type = Type.DRW_ACK
    signature : bytes = field(repr=False, kw_only=True, default=b'\xd1') # Signature byte. Must be 0xD1
    chan      : u8 # Channel index
    count     : u16 # Number of acks following
    acks      : list[u16] # Array of acknowledged DRW packet

    @classmethod
    def parse(cls, p):
        # not encrypted
        signature, p = Magic.parse(p, 1, b'\xd1')
        chan, p = u8.parse(p)
        count, p = u16.parse(p)
        acks, p = Array.parse(p, u16, count)

        return cls(signature=signature, chan=chan, count=count, acks=acks), p

    def pack(self):
        p  = Magic.pack(self.signature, 1, b'\xd1')
        p += u8.pack(self.chan)
        p += u16.pack(self.count)
        p += Array.pack(self.acks, u16, self.count)

        # not encrypted
        return super().pack(p)

@dataclass
class PktPunchTo(Message):
    type = Type.PUNCH_TO
    host : Host # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        host, p = Host.parse(p)

        return cls(host=host), p

    def pack(self):
        p  = Host.pack(self.host)

        # not encrypted
        return super().pack(p)

@dataclass
class PktHello(Message):
    type = Type.HELLO

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktLanSearch(Message):
    type = Type.LAN_SEARCH

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyHello(Message):
    type = Type.RLY_HELLO

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyHelloAck(Message):
    type = Type.RLY_HELLO_ACK

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyPort(Message):
    type = Type.RLY_PORT

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyPortAck(Message):
    type = Type.RLY_PORT_ACK
    mark : u32 # unknown
    port : u16 # unknown
    pad  : bytes = field(repr=False, kw_only=True, default='\x00' * 2) # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        mark, p = u32.parse(p)
        port, p = u16.parse(p)
        pad, p = Zeroes.parse(p, 2)

        return cls(mark=mark, port=port, pad=pad), p

    def pack(self):
        p  = u32.pack(self.mark)
        p += u16.pack(self.port)
        p += Zeroes.pack(self.pad, 2)

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyReq(Message):
    type = Type.RLY_REQ
    duid : Duid # unknown
    host : Host # unknown
    mark : u32 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)
        host, p = Host.parse(p)
        mark, p = u32.parse(p)

        return cls(duid=duid, host=host, mark=mark), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += Host.pack(self.host)
        p += u32.pack(self.mark)

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyReqAck(Message):
    type = Type.RLY_REQ_ACK
    mark : u32 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        mark, p = u32.parse(p)

        return cls(mark=mark), p

    def pack(self):
        p  = u32.pack(self.mark)

        # not encrypted
        return super().pack(p)

@dataclass
class PktAlive(Message):
    type = Type.ALIVE

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktAliveAck(Message):
    type = Type.ALIVE_ACK

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktClose(Message):
    type = Type.CLOSE

    @classmethod
    def parse(cls, p):
        # not encrypted

        return cls(), p

    def pack(self):
        p = b""

        # not encrypted
        return super().pack(p)

@dataclass
class PktHelloAck(Message):
    type = Type.HELLO_ACK
    host : Host # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        host, p = Host.parse(p)

        return cls(host=host), p

    def pack(self):
        p  = Host.pack(self.host)

        # not encrypted
        return super().pack(p)

@dataclass
class PktPunchPkt(Message):
    type = Type.PUNCH_PKT
    duid : Duid # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)

        return cls(duid=duid), p

    def pack(self):
        p  = Duid.pack(self.duid)

        # not encrypted
        return super().pack(p)

@dataclass
class PktP2pRdy(Message):
    type = Type.P2P_RDY
    duid : Duid # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)

        return cls(duid=duid), p

    def pack(self):
        p  = Duid.pack(self.duid)

        # not encrypted
        return super().pack(p)

@dataclass
class PktP2pReq(Message):
    type = Type.P2P_REQ
    duid : Duid # unknown
    host : Host # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)
        host, p = Host.parse(p)

        return cls(duid=duid, host=host), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += Host.pack(self.host)

        # not encrypted
        return super().pack(p)

@dataclass
class PktP2pReqAck(Message):
    type = Type.P2P_REQ_ACK
    mark : u32 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        mark, p = u32.parse(p)

        return cls(mark=mark), p

    def pack(self):
        p  = u32.pack(self.mark)

        # not encrypted
        return super().pack(p)

@dataclass
class PktP2pReqDsk(Message):
    type = Type.P2P_REQ_DSK
    duid     : Duid # unknown
    host     : Host # unknown
    nat_type : u8 # unknown
    version  : Version # unknown
    dsk      : Dsk # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)
        host, p = Host.parse(p)
        nat_type, p = u8.parse(p)
        version, p = Version.parse(p)
        dsk, p = Dsk.parse(p)

        return cls(duid=duid, host=host, nat_type=nat_type, version=version, dsk=dsk), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += Host.pack(self.host)
        p += u8.pack(self.nat_type)
        p += Version.pack(self.version)
        p += Dsk.pack(self.dsk)

        # not encrypted
        return super().pack(p)

@dataclass
class PktP2pRdyAck(Message):
    type = Type.P2P_RDY_ACK
    duid : Duid # unknown
    host : Host # unknown
    pad  : bytes = field(repr=False, kw_only=True, default='\x00' * 8) # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)
        host, p = Host.parse(p)
        pad, p = Zeroes.parse(p, 8)

        return cls(duid=duid, host=host, pad=pad), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += Host.pack(self.host)
        p += Zeroes.pack(self.pad, 8)

        # not encrypted
        return super().pack(p)

@dataclass
class PktListReqDsk(Message):
    type = Type.LIST_REQ_DSK
    duid : Duid # Device id
    dsk  : Dsk # Device secret key

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)
        dsk, p = Dsk.parse(p)

        return cls(duid=duid, dsk=dsk), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += Dsk.pack(self.dsk)

        # not encrypted
        return super().pack(p)

@dataclass
class PktListReqAck(Message):
    type = Type.LIST_REQ_ACK
    numr   : u8 # Number of relays
    pad    : bytes = field(repr=False, kw_only=True, default='\x00' * 3) # Padding
    relays : list[Host] # Available relay hosts

    @classmethod
    def parse(cls, p):
        # not encrypted
        numr, p = u8.parse(p)
        pad, p = Zeroes.parse(p, 3)
        relays, p = Array.parse(p, Host, numr)

        return cls(numr=numr, pad=pad, relays=relays), p

    def pack(self):
        p  = u8.pack(self.numr)
        p += Zeroes.pack(self.pad, 3)
        p += Array.pack(self.relays, Host, self.numr)

        # not encrypted
        return super().pack(p)

@dataclass
class PktDevLgnCrc(Message):
    type = Type.DEV_LGN_CRC
    duid     : Duid # unknown
    nat_type : u8 # unknown
    version  : Version # unknown
    host     : Host # unknown

    @classmethod
    def parse(cls, p):
        p = crypto_decurse_string(p)
        duid, p = Duid.parse(p)
        nat_type, p = u8.parse(p)
        version, p = Version.parse(p)
        host, p = Host.parse(p)

        return cls(duid=duid, nat_type=nat_type, version=version, host=host), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += u8.pack(self.nat_type)
        p += Version.pack(self.version)
        p += Host.pack(self.host)

        p = crypto_curse_string(p)
        return super().pack(p)

@dataclass
class PktRlyTo(Message):
    type = Type.RLY_TO
    host : Host # unknown
    mark : u32 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        host, p = Host.parse(p)
        mark, p = u32.parse(p)

        return cls(host=host, mark=mark), p

    def pack(self):
        p  = Host.pack(self.host)
        p += u32.pack(self.mark)

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyPkt(Message):
    type = Type.RLY_PKT
    mark : u32 # unknown
    duid : Duid # unknown
    unk  : u32 # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        mark, p = u32.parse(p)
        duid, p = Duid.parse(p)
        unk, p = u32.parse(p)

        return cls(mark=mark, duid=duid, unk=unk), p

    def pack(self):
        p  = u32.pack(self.mark)
        p += Duid.pack(self.duid)
        p += u32.pack(self.unk)

        # not encrypted
        return super().pack(p)

@dataclass
class PktRlyRdy(Message):
    type = Type.RLY_RDY
    duid : Duid # unknown

    @classmethod
    def parse(cls, p):
        # not encrypted
        duid, p = Duid.parse(p)

        return cls(duid=duid), p

    def pack(self):
        p  = Duid.pack(self.duid)

        # not encrypted
        return super().pack(p)

@dataclass
class PktDevLgnAckCrc(Message):
    type = Type.DEV_LGN_ACK_CRC
    pad0 : bytes = field(repr=False, kw_only=True, default='\x00' * 4) # unknown

    @classmethod
    def parse(cls, p):
        p = crypto_decurse_string(p)
        pad0, p = Zeroes.parse(p, 4)

        return cls(pad0=pad0), p

    def pack(self):
        p  = Zeroes.pack(self.pad0, 4)

        p = crypto_curse_string(p)
        return super().pack(p)

@dataclass
class PktSessionReady(Message):
    type = Type.REPORT_SESSION_READY
    duid           : Duid # unknown
    handle         : i32 # unknown
    max_handles    : u16 # unknown
    active_handles : u16 # unknown
    startup_ticks  : u16 # unknown
    b1             : u8 # unknown
    b2             : u8 # unknown
    b3             : u8 # unknown
    b4             : u8 # unknown
    pad0           : bytes = field(repr=False, kw_only=True, default='\x00' * 2) # unknown
    addr_local     : Host # unknown
    addr_wan       : Host # unknown
    addr_relay     : Host # unknown

    @classmethod
    def parse(cls, p):
        p = simple_decrypt_string(p)
        duid, p = Duid.parse(p)
        handle, p = i32.parse(p)
        max_handles, p = u16.parse(p)
        active_handles, p = u16.parse(p)
        startup_ticks, p = u16.parse(p)
        b1, p = u8.parse(p)
        b2, p = u8.parse(p)
        b3, p = u8.parse(p)
        b4, p = u8.parse(p)
        pad0, p = Zeroes.parse(p, 2)
        addr_local, p = Host.parse(p)
        addr_wan, p = Host.parse(p)
        addr_relay, p = Host.parse(p)

        return cls(duid=duid, handle=handle, max_handles=max_handles, active_handles=active_handles, startup_ticks=startup_ticks, b1=b1, b2=b2, b3=b3, b4=b4, pad0=pad0, addr_local=addr_local, addr_wan=addr_wan, addr_relay=addr_relay), p

    def pack(self):
        p  = Duid.pack(self.duid)
        p += i32.pack(self.handle)
        p += u16.pack(self.max_handles)
        p += u16.pack(self.active_handles)
        p += u16.pack(self.startup_ticks)
        p += u8.pack(self.b1)
        p += u8.pack(self.b2)
        p += u8.pack(self.b3)
        p += u8.pack(self.b4)
        p += Zeroes.pack(self.pad0, 2)
        p += Host.pack(self.addr_local)
        p += Host.pack(self.addr_wan)
        p += Host.pack(self.addr_relay)

        p = simple_encrypt_string(p)
        return super().pack(p)


MessageTypeTable = {
    Type.HELLO                : PktHello,
    Type.HELLO_ACK            : PktHelloAck,
    Type.DEV_LGN_CRC          : PktDevLgnCrc,
    Type.DEV_LGN_ACK_CRC      : PktDevLgnAckCrc,
    Type.P2P_REQ              : PktP2pReq,
    Type.P2P_REQ_ACK          : PktP2pReqAck,
    Type.P2P_REQ_DSK          : PktP2pReqDsk,
    Type.LAN_SEARCH           : PktLanSearch,
    Type.PUNCH_TO             : PktPunchTo,
    Type.PUNCH_PKT            : PktPunchPkt,
    Type.P2P_RDY              : PktP2pRdy,
    Type.P2P_RDY_ACK          : PktP2pRdyAck,
    Type.LIST_REQ_ACK         : PktListReqAck,
    Type.LIST_REQ_DSK         : PktListReqDsk,
    Type.RLY_HELLO            : PktRlyHello,
    Type.RLY_HELLO_ACK        : PktRlyHelloAck,
    Type.RLY_PORT             : PktRlyPort,
    Type.RLY_PORT_ACK         : PktRlyPortAck,
    Type.RLY_REQ              : PktRlyReq,
    Type.RLY_REQ_ACK          : PktRlyReqAck,
    Type.RLY_TO               : PktRlyTo,
    Type.RLY_PKT              : PktRlyPkt,
    Type.RLY_RDY              : PktRlyRdy,
    Type.DRW                  : PktDrw,
    Type.DRW_ACK              : PktDrwAck,
    Type.ALIVE                : PktAlive,
    Type.ALIVE_ACK            : PktAliveAck,
    Type.CLOSE                : PktClose,
    Type.REPORT_SESSION_READY : PktSessionReady,
}

