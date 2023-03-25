import paho.mqtt.client as mqtt
import paho.mqtt
import logging as log
import ssl
import json
import uuid

from libflagship.util import enhex
from libflagship.mqtt import MqttMsg, MqttPktType

class AnkerMQTTBaseClient:

    def __init__(self, printersn, mqtt, key, guid=None):
        self._mqtt = mqtt
        self._printersn = printersn
        self._key = key
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_publish = self.on_publish
        self._queue = []
        self._guid = guid or str(uuid.uuid4())

    # internal function
    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            raise IOError(f"could not connect: rc={rc} ({paho.mqtt.client.error_string(rc)})")
        mqtt = self._mqtt
        mqtt.subscribe(f"/phone/maker/{self.sn}/notice")
        mqtt.subscribe(f"/phone/maker/{self.sn}/command/reply")
        mqtt.subscribe(f"/phone/maker/{self.sn}/query/reply")
        self.on_connect(client, userdata, flags)

    # public api: override in subclass (if needed)
    def on_connect(self, client, userdata, flags):
        log.info("Connected to mqtt")


    # public api: override in subclass (if needed)
    def on_publish(self, client, userdata, result):
        pass


    # internal function
    def _on_message(self, client, userdata, msg):
        pkt, tail = MqttMsg.parse(msg.payload, key=self._key)

        data = json.loads(pkt.data)
        if isinstance(data, list):
            self._queue.append((msg, data))
        else:
            self._queue.append((msg, [data]))

        if tail:
            log.warning(f"UNPARSED TAIL DATA: {tail}")

        self.on_message(client, userdata, msg, pkt, tail)

    # public api: override in subclass (if needed)
    def on_message(self, client, userdata, msg, pkt, tail):
        pass


    @classmethod
    def login(cls, printersn, username, password, key, ca_certs="ankermake-mqtt.crt", verify=True):
        client = mqtt.Client()

        if verify:
            client.tls_set(ca_certs=ca_certs)
        else:
            client.tls_set(ca_certs=ca_certs, cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)

        client.username_pw_set(username, password)

        return cls(printersn, client, key)

    def connect(self, server, port=8789, timeout=60):
        self._mqtt.connect(server, port, timeout)

    @property
    def sn(self):
        return self._printersn

    def send_raw(self, topic, msg):
        payload = msg.pack(key=self._key)
        self._mqtt.publish(topic, payload=payload)

    @staticmethod
    def make_mqtt_pkt(guid, data, packet_type=MqttPktType.Single, packet_num=0):
        return MqttMsg(
            size=0, # fixed by .pack()
            m3=5,
            m4=1,
            m5=2,
            m6=5,
            m7=ord('F'),
            packet_type=MqttPktType.Single,
            packet_num=0,
            time=0,
            device_guid=guid,
            data=data,
        )

    def send(self, topic, msg):
        payload = self.make_mqtt_pkt(self._guid, json.dumps(msg).encode())
        log.debug(f"Sending mqtt command on [{topic}]: {payload}")
        return self.send_raw(topic, payload)

    def query(self, msg):
        return self.send(f"/device/maker/{self.sn}/query", msg)

    def command(self, msg):
        return self.send(f"/device/maker/{self.sn}/command", msg)

    def loop(self):
        self._mqtt.loop_forever()

    def fetch(self, timeout=1.0):
        self._mqtt.loop(timeout=timeout)
        return self.clearqueue()

    def fetchloop(self):
        while True:
            self._mqtt.loop(timeout=1.0)
            yield from self.clearqueue()

    def clearqueue(self):
        res = self._queue[:]
        self._queue.clear()
        return res
