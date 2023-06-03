import sys
import distro
import psutil
import cpuinfo
import platform

from flask import current_app as app
from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.system_info")
def machine_system_info():
    version_parts = distro.version_parts()
    cpuid = cpuinfo.CPUID()
    cpu_brand = cpuid.get_processor_brand(cpuid.get_max_extension_support())
    cpu_vendor = cpuid.get_vendor_id()

    return {
        "system_info": {
            "cpu_info": {
                "cpu_count": psutil.cpu_count(),
                "bits": platform.architecture()[0],
                "processor": platform.machine(),
                "cpu_desc": cpu_brand,
                "serial_number": "1337",
                "hardware_desc": cpu_vendor,
                "model": cpu_brand,
                "total_memory": psutil.virtual_memory().total // 1024,
                "memory_units": "kB"
            },
            "distribution": {
                "name": f"{distro.name()} {distro.version()} ({distro.codename()})",
                "id": distro.id(),
                "version": distro.version(),
                "version_parts": {
                    "major": str(version_parts[0]),
                    "minor": str(version_parts[1]),
                    "build_number": str(version_parts[2]),
                },
                "like": distro.like(),
                "codename": distro.codename(),
            },
            "available_services": [
                "klipper",
                "klipper_mcu",
                "moonraker",
            ],
            "instance_ids": {
                "moonraker": "moonraker",
                "klipper": "klipper"
            },
            "service_state": {
                "klipper": {
                    "active_state": "active",
                    "sub_state": "running"
                },
                "klipper_mcu": {
                    "active_state": "active",
                    "sub_state": "running"
                },
                "moonraker": {
                    "active_state": "active",
                    "sub_state": "running"
                }
            },
            "virtualization": {
                "virt_type": "none",
                "virt_identifier": "none"
            },
            "python": {
                "version": [
                    *platform.python_version_tuple(),
                    "final",
                    0
                ],
                "version_string": sys.version,
            },
            "network": {
                "wlan0": {
                    "mac_address": "<redacted_mac>",
                    "ip_addresses": [
                        {
                            "family": "ipv4",
                            "address": "192.168.1.127",
                            "is_link_local": False
                        },
                        {
                            "family": "ipv6",
                            "address": "<redacted_ipv6>",
                            "is_link_local": False
                        },
                        {
                            "family": "ipv6",
                            "address": "fe80::<redacted>",
                            "is_link_local": True
                        }
                    ]
                }
            },
            "canbus": {}
        }
    }


@dispatcher.add_method(name="machine.device_power.devices")
def machine_device_power_devices():
    return {
        "devices": []
    }


@dispatcher.add_method(name="machine.device_power.on")
def machine_device_power_on(**objs):
    return "ok"


@dispatcher.add_method(name="machine.proc_stats")
def machine_proc_stats():
    with app.svc.borrow("updates") as upd:
        sockets = len(upd.handlers)

    return {
        "moonraker_stats": [
            {
                "time": 1626612666.850755,
                "cpu_usage": 2.66,
                "memory": 24732,
                "mem_units": "kB"
            },
            {
                "time": 1626612667.8521338,
                "cpu_usage": 2.62,
                "memory": 24732,
                "mem_units": "kB"
            }
        ],
        "throttled_state": {
            "bits": 0,
            "flags": []
        },
        "cpu_temp": 42.0,
        "network": {
            "lo": {
                "rx_bytes": 113516429,
                "tx_bytes": 113516429,
                "bandwidth": 3342.68
            },
            "wlan0": {
                "rx_bytes": 48471767,
                "tx_bytes": 113430843,
                "bandwidth": 4455.91
            }
        },
        "system_cpu_usage": {
            "cpu": 2.53,
            "cpu0": 3.03,
            "cpu1": 5.1,
            "cpu2": 1.02,
            "cpu3": 1
        },
        "system_uptime": 2876970.38089603,
        "websocket_connections": sockets,
    }


@dispatcher.add_method(name="machine.services.restart")
def machine_services_restart(service):
    return "ok"


@dispatcher.add_method(name="machine.services.stop")
def machine_services_stop(service):
    return "ok"


@dispatcher.add_method(name="machine.services.start")
def machine_services_start(service):
    return "ok"


@dispatcher.add_method(name="machine.reboot")
def machine_reboot():
    return "ok"


@dispatcher.add_method(name="machine.shutdown")
def machine_shutdown():
    return "ok"
