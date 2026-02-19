"""Home Assistant MQTT Discovery service.

Connects to an external MQTT broker (typically Home Assistant's) and publishes
MQTT Discovery configuration payloads so the printer appears as a device with
sensors, a camera entity, and a light switch in Home Assistant.

State updates are published whenever the MQTT service forwards new data.
"""

import json
import logging as log
import os
import threading
import time

import paho.mqtt.client as paho_mqtt


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 1883
_DEFAULT_DISCOVERY_PREFIX = "homeassistant"
_DEFAULT_TOPIC_PREFIX = "ankerctl"
_AVAILABILITY_TIMEOUT = 60  # seconds between availability pings


class HomeAssistantService:
    """Bridges ankerctl printer data to Home Assistant via MQTT Discovery."""

    def __init__(self, config_manager, printer_sn=None, printer_name=None):
        self._config_manager = config_manager
        self._printer_sn = printer_sn or "ankerctl"
        self._printer_name = printer_name or "AnkerMake M5"
        self._node_id = f"ankerctl_{self._printer_sn}"

        self._client = None
        self._connected = False
        self._lock = threading.Lock()
        self._availability_thread = None
        self._stop_event = threading.Event()

        # Cached state for publishing
        self._state = {
            "print_progress": None,
            "print_status": "idle",
            "nozzle_temp": None,
            "nozzle_temp_target": None,
            "bed_temp": None,
            "bed_temp_target": None,
            "print_speed": None,
            "print_layer": None,
            "print_filename": None,
            "time_elapsed": None,
            "time_remaining": None,
            "mqtt_connected": False,
            "pppp_connected": False,
            "light": False,
        }

        # Set defaults
        self._enabled = False
        self._host = _DEFAULT_HOST
        self._port = _DEFAULT_PORT
        self._user = ""
        self._password = ""
        self._discovery_prefix = _DEFAULT_DISCOVERY_PREFIX
        self._topic_prefix = _DEFAULT_TOPIC_PREFIX

        self.reload_config()

    def reload_config(self, config=None):
        # If no config passed, use stored config_manager
        if config is None:
            config = self._config_manager

        # If config is a ConfigManager (has .open() method), load the actual config
        if config and hasattr(config, 'open'):
            with config.open() as cfg:
                config = cfg

        if not config or not getattr(config, 'home_assistant', None):
            return

        cfg = config.home_assistant
        new_enabled = cfg.get("enabled", False)
        new_host = cfg.get("mqtt_host", _DEFAULT_HOST)
        new_port = int(cfg.get("mqtt_port", _DEFAULT_PORT))
        new_user = cfg.get("mqtt_username", "")
        new_password = cfg.get("mqtt_password", "")
        new_discovery_prefix = cfg.get("discovery_prefix", _DEFAULT_DISCOVERY_PREFIX)
        # topic prefix is not in config model yet? Defaults to ankerctl
        new_topic_prefix = os.getenv("HA_MQTT_TOPIC_PREFIX", _DEFAULT_TOPIC_PREFIX)

        # check if restart needed
        need_restart = False
        if self._client: # Only if currently running
            if (self._host != new_host or 
                self._port != new_port or 
                self._user != new_user or 
                self._password != new_password or
                self._discovery_prefix != new_discovery_prefix or
                self._topic_prefix != new_topic_prefix):
                need_restart = True
            if self._enabled and not new_enabled:
                self.stop() # Just stop
                need_restart = False

        self._enabled = new_enabled
        self._host = new_host
        self._port = new_port
        self._user = new_user
        self._password = new_password
        self._discovery_prefix = new_discovery_prefix
        self._topic_prefix = new_topic_prefix

        if need_restart and self._enabled:
            self.stop()
            self.start()
        elif self._enabled and not self._client:
            # If enabled and not running, start? 
            # MqttQueue calls start() explicitly.
            # But if we are called at runtime (API update), we might need to start it.
            # We'll assume if it was meant to be running, start it.
            pass

    @property
    def enabled(self):
        return self._enabled

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Connect to the HA MQTT broker and publish discovery configs."""
        if not self._enabled:
            return

        log.info(f"HA MQTT: connecting to {self._host}:{self._port}")
        self._client = paho_mqtt.Client(client_id=f"ankerctl-{self._printer_sn}", clean_session=True)

        if self._user:
            self._client.username_pw_set(self._user, self._password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Set LWT (Last Will and Testament) so HA marks device offline
        avail_topic = self._availability_topic()
        self._client.will_set(avail_topic, payload="offline", qos=1, retain=True)

        try:
            self._client.connect(self._host, self._port, keepalive=60)
            self._client.loop_start()
        except Exception as err:
            log.error(f"HA MQTT: connection failed: {err}")
            self._client = None

    def stop(self):
        """Disconnect from the HA MQTT broker and mark device offline."""
        if not self._client:
            return

        self._stop_event.set()
        if self._availability_thread and self._availability_thread.is_alive():
            self._availability_thread.join(timeout=5)

        try:
            self._publish(self._availability_topic(), "offline", retain=True)
            self._client.disconnect()
            self._client.loop_stop()
        except Exception as err:
            log.warning(f"HA MQTT: disconnect error: {err}")
        finally:
            self._client = None
            self._connected = False

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            log.error(f"HA MQTT: connection refused (rc={rc})")
            return

        log.info("HA MQTT: connected to broker")
        self._connected = True

        # Publish discovery configs
        self._publish_discovery()

        # Mark device online
        self._publish(self._availability_topic(), "online", retain=True)

        # Subscribe to command topics (light switch)
        light_cmd_topic = f"{self._topic_prefix}/{self._printer_sn}/light/set"
        client.subscribe(light_cmd_topic, qos=1)
        log.info(f"HA MQTT: subscribed to {light_cmd_topic}")

        # Start availability heartbeat
        self._stop_event.clear()
        self._availability_thread = threading.Thread(
            target=self._availability_loop, daemon=True, name="ha-mqtt-avail"
        )
        self._availability_thread.start()

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            log.warning(f"HA MQTT: unexpected disconnect (rc={rc}), will auto-reconnect")
        else:
            log.info("HA MQTT: disconnected")

    def _on_message(self, client, userdata, msg):
        """Handle incoming commands from Home Assistant (e.g. light switch)."""
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        log.info(f"HA MQTT: received {topic} = {payload}")

        light_cmd_topic = f"{self._topic_prefix}/{self._printer_sn}/light/set"
        if topic == light_cmd_topic:
            self._handle_light_command(payload)

    def _handle_light_command(self, payload):
        """Forward light on/off command to the printer via the web service."""
        try:
            from web import app
            vq = app.svc.svcs.get("videoqueue")
            if vq:
                turn_on = payload.upper() == "ON"
                vq.api_light_state(turn_on)
                self._state["light"] = turn_on
                self._publish_state()
                log.info(f"HA MQTT: light {'ON' if turn_on else 'OFF'}")
            else:
                log.warning("HA MQTT: videoqueue not available for light control")
        except Exception as err:
            log.warning(f"HA MQTT: light command failed: {err}")

    # ------------------------------------------------------------------
    # State update API (called from mqtt.py)
    # ------------------------------------------------------------------

    def update_state(self, **kwargs):
        """Update cached state and publish to HA.

        Accepts keyword arguments matching state keys:
            print_progress, print_status, nozzle_temp, nozzle_temp_target,
            bed_temp, bed_temp_target, print_speed, print_layer,
            print_filename, time_elapsed, time_remaining,
            mqtt_connected, pppp_connected, light
        """
        if not self._enabled or not self._connected:
            return

        changed = False
        for key, value in kwargs.items():
            if key in self._state and self._state[key] != value:
                self._state[key] = value
                changed = True

        if changed:
            self._publish_state()

    # ------------------------------------------------------------------
    # MQTT Publishing
    # ------------------------------------------------------------------

    def _publish(self, topic, payload, retain=False, qos=0):
        """Publish a message, handling errors gracefully."""
        if not self._client or not self._connected:
            return
        try:
            self._client.publish(topic, payload, qos=qos, retain=retain)
        except Exception as err:
            log.warning(f"HA MQTT: publish failed on {topic}: {err}")

    def _availability_topic(self):
        return f"{self._topic_prefix}/{self._printer_sn}/availability"

    def _state_topic(self):
        return f"{self._topic_prefix}/{self._printer_sn}/state"

    def _availability_loop(self):
        """Periodically publish availability to keep HA happy."""
        while not self._stop_event.is_set():
            self._publish(self._availability_topic(), "online", retain=True)
            self._stop_event.wait(_AVAILABILITY_TIMEOUT)

    def _publish_state(self):
        """Publish the full state JSON to the state topic."""
        payload = json.dumps(self._state)
        self._publish(self._state_topic(), payload, retain=True)

    # ------------------------------------------------------------------
    # MQTT Discovery
    # ------------------------------------------------------------------

    def _device_info(self):
        """Return the HA device registry block."""
        return {
            "identifiers": [self._node_id],
            "name": self._printer_name,
            "manufacturer": "AnkerMake",
            "model": "M5",
            "sw_version": "ankerctl",
        }

    def _availability_config(self):
        """Return the availability block for discovery payloads."""
        return [{
            "topic": self._availability_topic(),
            "payload_available": "online",
            "payload_not_available": "offline",
        }]

    def _publish_discovery(self):
        """Publish all MQTT Discovery config payloads."""
        state_topic = self._state_topic()
        device = self._device_info()
        availability = self._availability_config()

        sensors = [
            {
                "id": "print_progress",
                "name": "Print Progress",
                "unit": "%",
                "icon": "mdi:printer-3d",
                "value_template": "{{ value_json.print_progress | default(0) }}",
            },
            {
                "id": "print_status",
                "name": "Print Status",
                "icon": "mdi:printer-3d-nozzle",
                "value_template": "{{ value_json.print_status | default('idle') }}",
            },
            {
                "id": "nozzle_temp",
                "name": "Nozzle Temperature",
                "unit": "\u00b0C",
                "device_class": "temperature",
                "value_template": "{{ value_json.nozzle_temp | default(0) }}",
            },
            {
                "id": "nozzle_temp_target",
                "name": "Nozzle Target",
                "unit": "\u00b0C",
                "device_class": "temperature",
                "value_template": "{{ value_json.nozzle_temp_target | default(0) }}",
            },
            {
                "id": "bed_temp",
                "name": "Bed Temperature",
                "unit": "\u00b0C",
                "device_class": "temperature",
                "value_template": "{{ value_json.bed_temp | default(0) }}",
            },
            {
                "id": "bed_temp_target",
                "name": "Bed Target",
                "unit": "\u00b0C",
                "device_class": "temperature",
                "value_template": "{{ value_json.bed_temp_target | default(0) }}",
            },
            {
                "id": "print_speed",
                "name": "Print Speed",
                "unit": "mm/s",
                "icon": "mdi:speedometer",
                "value_template": "{{ value_json.print_speed | default(0) }}",
            },
            {
                "id": "print_layer",
                "name": "Print Layer",
                "icon": "mdi:layers",
                "value_template": "{{ value_json.print_layer | default('') }}",
            },
            {
                "id": "print_filename",
                "name": "Print Filename",
                "icon": "mdi:file",
                "value_template": "{{ value_json.print_filename | default('') }}",
            },
            {
                "id": "time_elapsed",
                "name": "Time Elapsed",
                "unit": "s",
                "device_class": "duration",
                "value_template": "{{ value_json.time_elapsed | default(0) }}",
            },
            {
                "id": "time_remaining",
                "name": "Time Remaining",
                "unit": "s",
                "device_class": "duration",
                "value_template": "{{ value_json.time_remaining | default(0) }}",
            },
        ]

        for sensor in sensors:
            config = {
                "name": sensor["name"],
                "unique_id": f"{self._node_id}_{sensor['id']}",
                "object_id": f"{self._node_id}_{sensor['id']}",
                "state_topic": state_topic,
                "value_template": sensor["value_template"],
                "device": device,
                "availability": availability,
            }
            if "unit" in sensor:
                config["unit_of_measurement"] = sensor["unit"]
            if "device_class" in sensor:
                config["device_class"] = sensor["device_class"]
            if "icon" in sensor:
                config["icon"] = sensor["icon"]

            topic = f"{self._discovery_prefix}/sensor/{self._node_id}/{sensor['id']}/config"
            self._publish(topic, json.dumps(config), retain=True)

        # Binary sensors: mqtt_connected, pppp_connected
        binary_sensors = [
            {
                "id": "mqtt_connected",
                "name": "MQTT Connected",
                "device_class": "connectivity",
                "value_template": "{{ 'ON' if value_json.mqtt_connected else 'OFF' }}",
            },
            {
                "id": "pppp_connected",
                "name": "PPPP Connected",
                "device_class": "connectivity",
                "value_template": "{{ 'ON' if value_json.pppp_connected else 'OFF' }}",
            },
        ]

        for bs in binary_sensors:
            config = {
                "name": bs["name"],
                "unique_id": f"{self._node_id}_{bs['id']}",
                "object_id": f"{self._node_id}_{bs['id']}",
                "state_topic": state_topic,
                "value_template": bs["value_template"],
                "device_class": bs["device_class"],
                "payload_on": "ON",
                "payload_off": "OFF",
                "device": device,
                "availability": availability,
            }
            topic = f"{self._discovery_prefix}/binary_sensor/{self._node_id}/{bs['id']}/config"
            self._publish(topic, json.dumps(config), retain=True)

        # Light switch
        light_config = {
            "name": "Printer Light",
            "unique_id": f"{self._node_id}_light",
            "object_id": f"{self._node_id}_light",
            "state_topic": state_topic,
            "command_topic": f"{self._topic_prefix}/{self._printer_sn}/light/set",
            "value_template": "{{ 'ON' if value_json.light else 'OFF' }}",
            "payload_on": "ON",
            "payload_off": "OFF",
            "icon": "mdi:lightbulb",
            "device": device,
            "availability": availability,
        }
        topic = f"{self._discovery_prefix}/switch/{self._node_id}/light/config"
        self._publish(topic, json.dumps(light_config), retain=True)

        # Camera entity (MJPEG stream)
        flask_host = os.getenv("FLASK_HOST") or "127.0.0.1"
        if flask_host in ("0.0.0.0", "::"):
            flask_host = "127.0.0.1"
        flask_port = os.getenv("FLASK_PORT") or "4470"
        camera_config = {
            "name": "Camera",
            "unique_id": f"{self._node_id}_camera",
            "object_id": f"{self._node_id}_camera",
            "topic": f"{self._topic_prefix}/{self._printer_sn}/camera",
            "device": device,
            "availability": availability,
            "icon": "mdi:camera",
        }
        topic = f"{self._discovery_prefix}/camera/{self._node_id}/camera/config"
        self._publish(topic, json.dumps(camera_config), retain=True)

        log.info(f"HA MQTT: published discovery configs ({len(sensors)} sensors, "
                 f"{len(binary_sensors)} binary sensors, 1 switch, 1 camera)")
