import time
import psutil
import logging as log

from datetime import datetime
from flask import current_app as app
from jsonrpc import dispatcher

from libflagship.mqtt import MqttMsgType

from ...lib.gcode import GCode


@dispatcher.add_method(name="printer.print.start")
def printer_print_start(filename):
    with app.svc.borrow("updates") as upd:
        upd.umgr.print_stats.state = "printing"

    return "ok"


@dispatcher.add_method(name="printer.print.pause")
def printer_print_pause():
    with app.svc.borrow("updates") as upd:
        upd.umgr.print_stats.state = "paused"
        upd.umgr.display_status.progress = None

    return "ok"


@dispatcher.add_method(name="printer.print.resume")
def printer_print_resume():
    with app.svc.borrow("updates") as upd:
        upd.umgr.print_stats.state = "printing"

    return "ok"


@dispatcher.add_method(name="printer.print.cancel")
def printer_print_cancel():
    with app.svc.borrow("updates") as upd:
        upd.umgr.print_stats.state = "ready"
        upd.umgr.print_stats.filename = None

    return "ok"


@dispatcher.add_method(name="printer.emergency_stop")
def printer_emergency_stop():
    return "ok"


@dispatcher.add_method(name="printer.restart")
def printer_restart():
    raise NotImplementedError()


@dispatcher.add_method(name="printer.firmware_restart")
def printer_firmware_restart():
    raise NotImplementedError()


@dispatcher.add_method(name="printer.objects.list")
def printer_objects_list():
    with app.svc.borrow("updates") as upd:
        objs = upd.umgr.moonraker_object_list()

    return {
        "objects": [
            *objs,
            "gcode_macro START_PRINT",
            "gcode_macro END_PRINT",
            "gcode_macro CANCEL_PRINT",
            "gcode_macro PAUSE",
            "gcode_macro RESUME",
            "gcode_macro M117",
            "gcode_macro M600",
            "gcode_macro LOAD_FILAMENT",
            "gcode_macro UNLOAD_FILAMENT",
            "gcode_macro M104",
            "gcode_macro M109",
            "gcode_macro M140",
            "gcode_macro M190",
            "gcode_macro ANKERMAKE_LIGHT_ON",
            "gcode_macro ANKERMAKE_LIGHT_OFF",
        ]
    }


@dispatcher.add_method(name="printer.objects.subscribe")
def printer_objects_subscribe(objects):
    return printer_objects_query(objects)


@dispatcher.add_method(name="printer.objects.query")
def printer_objects_query(objects):
    with app.svc.borrow("updates") as upd:
        status = upd.umgr.moonraker_status_full()

    return {
        "eventtime": datetime.now().timestamp(),
        "status": {
            **status,
            "configfile": {
                "config": {
                    "timelapse": {},
                    "pause_resume": {},
                    "display_status": {},
                    "exclude_object": {},
                    "virtual_sdcard": {},
                    "heater_bed": {
                        "min_temp": 0,
                        "max_temp": 100,
                    },
                    "bed_mesh": {},
                    "extruder": {
                        "min_temp": 0,
                        "max_temp": 260,
                        "min_extrude_temp": 165,
                    },
                    "gcode_macro START_PRINT": {
                        "description": "G-Code macro",
                        "gcode": "\nM117 START_PRINT called with {rawparams}\nG28"
                    },
                    "gcode_macro END_PRINT": {
                        "description": "G-Code macro",
                        "gcode": "\nM117 END_PRINT called with {rawparams}"
                    },
                    "gcode_macro CANCEL_PRINT": {
                        "rename_existing": "CANCEL_PRINT_BASE",
                        "description": "G-Code macro",
                        "gcode": "\nM117 CANCEL_PRINT called with {rawparams}\nCANCEL_PRINT_BASE"
                    },
                    "gcode_macro PAUSE": {
                        "rename_existing": "PAUSE_BASE",
                        "description": "G-Code macro",
                        "gcode": "\nM117 PAUSE called with {rawparams}\nPAUSE_BASE"
                    },
                    "gcode_macro RESUME": {
                        "rename_existing": "RESUME_BASE",
                        "description": "G-Code macro",
                        "gcode": "\nM117 RESUME called with {rawparams}\nRESUME_BASE"
                    },
                    "gcode_macro M117": {
                        "rename_existing": "M117.1",
                        "description": "G-Code macro",
                        "gcode": "\nM117.1 {rawparams}\n{action_respond_info(rawparams)}"
                    },
                    "gcode_macro M600": {
                        "description": "G-Code macro",
                        "gcode": "\nM117 M600 called with {rawparams}\nPAUSE"
                    },
                    "gcode_macro LOAD_FILAMENT": {
                        "description": "G-Code macro",
                        "gcode": "\nM117 Loading Filament! Please wait..."
                    },
                    "gcode_macro UNLOAD_FILAMENT": {
                        "description": "G-Code macro",
                        "gcode": "\nM117 Unloading Filament! Please wait..."
                    },
                    "gcode_macro M104": {
                        "rename_existing": "M104.1",
                        "description": "G-Code macro",
                        "gcode": "\nM117 M104 called with {rawparams}"
                    },
                    "gcode_macro M109": {
                        "rename_existing": "M109.1",
                        "description": "G-Code macro",
                        "gcode": "\nM117 M109 called with {rawparams}"
                    },
                    "gcode_macro ANKERCTL_LIGHT_ON": {
                        "gcode": "\nANKERCTL_LIGHT_ON {rawparams}",
                        "description": "G-Code macro"
                    },
                    "gcode_macro ANKERCTL_LIGHT_OFF": {
                        "gcode": "\nANKERCTL_LIGHT_OFF {rawparams}",
                        "description": "G-Code macro"
                    },
                },
                "settings": {
                    "timelapse": {},
                    "gcode_macro start_print": {
                        "gcode": "\nM117 START_PRINT called with {rawparams}\nG28",
                        "description": "G-Code macro"
                    },
                    "gcode_macro end_print": {
                        "gcode": "\nM117 END_PRINT called with {rawparams}",
                        "description": "G-Code macro"
                    },
                    "gcode_macro cancel_print": {
                        "gcode": "\nM117 CANCEL_PRINT called with {rawparams}\nCANCEL_PRINT_BASE",
                        "rename_existing": "CANCEL_PRINT_BASE",
                        "description": "G-Code macro"
                    },
                    "gcode_macro pause": {
                        "gcode": "\nM117 PAUSE called with {rawparams}\nPAUSE_BASE",
                        "rename_existing": "PAUSE_BASE",
                        "description": "G-Code macro"
                    },
                    "gcode_macro resume": {
                        "gcode": "\nM117 RESUME called with {rawparams}\nRESUME_BASE",
                        "rename_existing": "RESUME_BASE",
                        "description": "G-Code macro"
                    },
                    "gcode_macro m117": {
                        "gcode": "\nM117.1 {rawparams}\n{action_respond_info(rawparams)}",
                        "rename_existing": "M117.1",
                        "description": "G-Code macro"
                    },
                    "gcode_macro m600": {
                        "gcode": "\nM117 M600 called with {rawparams}\nPAUSE",
                        "description": "G-Code macro"
                    },
                    "gcode_macro load_filament": {
                        "gcode": "\nM117 Loading Filament! Please wait...",
                        "description": "G-Code macro"
                    },
                    "gcode_macro unload_filament": {
                        "gcode": "\nM117 Unloading Filament! Please wait...",
                        "description": "G-Code macro"
                    },
                    "gcode_macro m104": {
                        "gcode": "\nM117 M104 called with {rawparams}",
                        "rename_existing": "M104.1",
                        "description": "G-Code macro"
                    },
                    "gcode_macro m109": {
                        "gcode": "\nM117 M109 called with {rawparams}",
                        "rename_existing": "M109.1",
                        "description": "G-Code macro"
                    },
                    "gcode_macro ankerctl_light_on": {
                        "gcode": "\nANKERCTL_LIGHT_ON {rawparams}",
                        "description": "G-Code macro"
                    },
                    "gcode_macro ankerctl_light_off": {
                        "gcode": "\nANKERCTL_LIGHT_OFF {rawparams}",
                        "description": "G-Code macro"
                    },
                    "bed_mesh": {},
                    "extruder": {},
                },
                "warnings": [],
                "save_config_pending": False,
                "save_config_pending_items": {}
            },
            "gcode_macro START_PRINT": {},
            "gcode_macro END_PRINT": {},
            "gcode_macro CANCEL_PRINT": {},
            "gcode_macro PAUSE": {},
            "gcode_macro RESUME": {},
            "gcode_macro M117": {},
            "gcode_macro M600": {},
            "gcode_macro LOAD_FILAMENT": {},
            "gcode_macro UNLOAD_FILAMENT": {},
            "gcode_macro M104": {},
            "gcode_macro M109": {},
            "gcode_macro M140": {},
            "gcode_macro M190": {},
            "gcode_macro ANKERMAKE_LIGHT_ON": {},
            "gcode_macro ANKERMAKE_LIGHT_OFF": {},
            "system_stats": {
                "sysload": psutil.getloadavg()[0],
                "cputime": psutil.cpu_times().user,
                "memavail": psutil.virtual_memory().available / 1024.0,
            },
        }
    }


@dispatcher.add_method(name="printer.query_endstops.status")
def printer_query_endstops_status():
    # There's no known way to really query endstops on the M5
    return {
        # "x": "TRIGGERED",
        # "y": "open",
        # "z": "open"
    }


@dispatcher.add_method(name="printer.info")
def printer_info():
    return {
        "state": "ready",
        "state_message": "Printer is ready",
        "hostname": "265f04e5466d",
        "klipper_path": "/home/printer/klipper",
        "python_path": "/home/printer/klippy-env/bin/python",
        "log_file": "/home/printer/printer_data/logs/klippy.log",
        "config_file": "/home/printer/printer_data/config/printer.cfg",
        "software_version": "v0.11.0-173-ga8b1b0ef",
        "cpu_info": "42 core AMD Ryzen 11 1337X 42-Core Processor"
    }


@dispatcher.add_method(name="printer.gcode.help")
def printer_gcode_help():
    return {
        "CUSTOM": "yep"
    }


@dispatcher.add_method(name="printer.gcode.script")
def printer_gcode_script(script):
    gcode = GCode(script)

    if gcode.cmd == "SET_HEATER_TEMPERATURE":
        with app.svc.borrow("updates") as upd:
            pstate = upd.pstate

        match gcode.vals["HEATER"]:
            case "extruder":   pstate.nozzle.target = float(gcode.vals["TARGET"])
            case "heater_bed": pstate.hotbed.target = float(gcode.vals["TARGET"])


        with app.svc.borrow("mqttqueue") as mqttq:
            mqttq.api_command(
                MqttMsgType.ZZ_MQTT_CMD_PREHEAT_CONFIG,
                value=int(bool(pstate.nozzle.target or pstate.hotbed.target)),
                nozzle=int(pstate.nozzle.target * 100),
                heatbed=int(pstate.hotbed.target * 100),
            )

    elif gcode.cmd == "M117":
        with app.svc.borrow("updates") as upd:
            upd.umgr.display_status.message = " ".join(gcode.args)

    elif gcode.cmd == "ANKERCTL_LIGHT_ON":
        with app.svc.borrow("videoqueue") as vq:
            vq.api_light_state(True)

    elif gcode.cmd == "ANKERCTL_LIGHT_OFF":
        with app.svc.borrow("videoqueue") as vq:
            vq.api_light_state(False)

    elif gcode.cmd == "BED_MESH_PROFILE":
        with app.svc.borrow("mqttqueue") as mqttq:
            if gcode.vals.get("LOAD") == "ankermake-builtin":
                mqttq.api_gcode("M420 V1")
            else:
                log.error(f"Unsupported gcode: {gcode}")

    else:
        with app.svc.borrow("mqttqueue") as mqttq:
            for line in script.splitlines():
                mqttq.api_gcode(line)
                time.sleep(0.2)

    return "ok"
