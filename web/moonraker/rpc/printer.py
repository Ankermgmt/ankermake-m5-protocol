import psutil

from flask import current_app as app
from jsonrpc import dispatcher

from libflagship.mqtt import MqttMsgType

from ...lib.gcode import GCode


@dispatcher.add_method(name="printer.print.start")
def printer_print_start(filename):
    with app.svc.borrow("updates") as upd:
        upd.notify_status_update(**{
            "print_stats": {
                "state": "printing",
            },
        }
    )
    return "ok"


@dispatcher.add_method(name="printer.print.pause")
def printer_print_pause():
    with app.svc.borrow("updates") as upd:
        upd.notify_status_update(**{
            "display_status": {
                "progress": None,
            },
            "print_stats": {
                "state": "paused",
            },
        }
    )
    return "ok"


@dispatcher.add_method(name="printer.print.resume")
def printer_print_resume():
    with app.svc.borrow("updates") as upd:
        upd.notify_status_update(**{
            "print_stats": {
                "state": "printing",
            },
        }
    )
    return "ok"


@dispatcher.add_method(name="printer.print.cancel")
def printer_print_cancel():
    with app.svc.borrow("updates") as upd:
        upd.notify_status_update(**{
            "print_stats": {
                "state": "ready",
                "filename": None,
            },
        }
    )
    return "ok"


@dispatcher.add_method(name="printer.emergency_stop")
def printer_emergency_stop():
    return "ok"


@dispatcher.add_method(name="printer.objects.list")
def printer_objects_list():
    return {
        "objects": [
            "webhooks",
            "configfile",
            "mcu",
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
            "heaters",
            "heater_bed",
            "gcode_macro M140",
            "gcode_macro M190",
            "gcode_macro ANKERMAKE_LIGHT_ON",
            "gcode_macro ANKERMAKE_LIGHT_OFF",
            "fan",
            "heater_fan heater_fan",
            "stepper_enable",
            "controller_fan controller_fan",
            "pause_resume",
            "display_status",
            "gcode_move",
            "exclude_object",
            "print_stats",
            "bed_mesh",
            "motion_report",
            "idle_timeout",
            "system_stats",
            "toolhead",
            "extruder"
        ]
    }


@dispatcher.add_method(name="printer.objects.subscribe")
def printer_objects_subscribe(objects):
    with app.svc.borrow("updates") as upd:
        pstate = upd.pstate

    return {
        "eventtime": 3793707.88993766,
        "status": {
            "webhooks": {
                "state": "ready",
                "state_message": "Printer is ready"
            },
            "print_stats": {
                "filename": "",
                "total_duration": 0,
                "print_duration": 0,
                "filament_used": 0,
                "state": "standby",
                "message": "",
                "info": {
                    "total_layer": None,
                    "current_layer": None
                }
            },
            "heater_bed": {
                "temperature": pstate.hotbed.current,
                "target": pstate.hotbed.target,
                "power": 0
            },
            "extruder": {
                "temperature": pstate.nozzle.current,
                "target": pstate.nozzle.target,
                "power": 0,
                "can_extrude": True,
                "pressure_advance": 0.1,
                "smooth_time": 0.01,
                "motion_queue": None
            },
            "heaters": {
                "available_heaters": [
                    "heater_bed",
                    "extruder"
                ],
                "available_sensors": [
                    "heater_bed",
                    "extruder"
                ]
            },
            "fan": {
                "speed": 0,
                "rpm": None
            },
            "heater_fan heater_fan": {
                "speed": 1,
                "rpm": None
            },
            "display_status": {
                "progress": 0,
                "message": "Greetings, Professor Falken"
            },
            "idle_timeout": {
                "state": "Idle",
                "printing_time": 0
            },
            "toolhead": {
                "homed_axes": "",
                "axis_minimum": [
                    -15,
                    -15,
                    -2,
                    0
                ],
                "axis_maximum": [
                    235,
                    235,
                    250,
                    0
                ],
                "print_time": 0.005,
                "stalls": 0,
                "estimated_print_time": 166.10390085,
                "extruder": "extruder",
                "position": [
                    0,
                    0,
                    0,
                    0
                ],
                "max_velocity": 300,
                "max_accel": 3000,
                "max_accel_to_decel": 1500,
                "square_corner_velocity": 5
            },
            "configfile": {
                "config": {
                    "pause_resume": {},
                    "display_status": {},
                    "exclude_object": {},
                    "virtual_sdcard": {},
                    "gcode_macro START_PRINT": {
                        "gcode": "\nM117 START_PRINT called with {rawparams}\nG28"
                    },
                    "gcode_macro END_PRINT": {
                        "gcode": "\nM117 END_PRINT called with {rawparams}"
                    },
                    "gcode_macro CANCEL_PRINT": {
                        "rename_existing": "CANCEL_PRINT_BASE",
                        "gcode": "\nM117 CANCEL_PRINT called with {rawparams}\nCANCEL_PRINT_BASE"
                    },
                    "gcode_macro PAUSE": {
                        "rename_existing": "PAUSE_BASE",
                        "gcode": "\nM117 PAUSE called with {rawparams}\nPAUSE_BASE"
                    },
                    "gcode_macro RESUME": {
                        "rename_existing": "RESUME_BASE",
                        "gcode": "\nM117 RESUME called with {rawparams}\nRESUME_BASE"
                    },
                    "gcode_macro M117": {
                        "rename_existing": "M117.1",
                        "gcode": "\nM117.1 {rawparams}\n{action_respond_info(rawparams)}"
                    },
                    "gcode_macro M600": {
                        "gcode": "\nM117 M600 called with {rawparams}\nPAUSE"
                    },
                    "gcode_macro LOAD_FILAMENT": {
                        "gcode": "\nM117 Loading Filament! Please wait..."
                    },
                    "gcode_macro UNLOAD_FILAMENT": {
                        "gcode": "\nM117 Unloading Filament! Please wait..."
                    },
                    "gcode_macro M104": {
                        "rename_existing": "M104.1",
                        "gcode": "\nM117 M104 called with {rawparams}"
                    },
                    "gcode_macro M109": {
                        "rename_existing": "M109.1",
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
                },
                "warnings": [],
                "save_config_pending": False,
                "save_config_pending_items": {}
            },
            "mcu": {
                "mcu_version": "Linux 4.4.94",
                "mcu_build_versions": "Ingenic r4.1.1-gcc720-glibc226-fp64 2020.11-05",
                "mcu_constants": {},
                "last_stats": {},
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
            "stepper_enable": {
                "steppers": {
                    "stepper_x": False,
                    "stepper_y": False,
                    "stepper_z": False,
                    "extruder": False
                }
            },
            "controller_fan controller_fan": {
                "speed": 0,
                "rpm": None
            },
            "gcode_move": {
                "speed_factor": 1,
                "speed": 1500,
                "extrude_factor": 1,
                "absolute_coordinates": True,
                "absolute_extrude": True,
                "homing_origin": [
                    0,
                    0,
                    0,
                    0
                ],
                "position": [
                    0,
                    0,
                    0,
                    0
                ],
                "gcode_position": [
                    0,
                    0,
                    0,
                    0
                ]
            },
            "exclude_object": {
                "objects": [],
                "excluded_objects": [],
                "current_object": None
            },
            "bed_mesh": {
                "profile_name": "",
                "mesh_min": [
                    0,
                    0
                ],
                "mesh_max": [
                    0,
                    0
                ],
                "probed_matrix": [
                    []
                ],
                "mesh_matrix": [
                    []
                ],
                "profiles": {
                    "default": {
                        "points": [
                            [0.075, 0.069792, 0.062708, 0.044167, 0.032917],
                            [0.045417, 0.043958, 0.066042, 0.053333, 0.03875],
                            [0.034375, 0.023333, 0.032917, 0.054167, 0.043542],
                            [0.076042, 0.056458, 0.06625, 0.045, 0.057292],
                            [0.051875, 0.036875, 0.03, 0.020625, 0.043125]
                        ],
                        "mesh_params": {
                            "min_x": 10,
                            "max_x": 225,
                            "min_y": 10,
                            "max_y": 225,
                            "x_count": 5,
                            "y_count": 5,
                            "mesh_x_pps": 5,
                            "mesh_y_pps": 5,
                            "algo": "bicubic",
                            "tension": 0.2
                        }
                    },
                    "mesh_profile_2": {
                        "points": [
                            [0.025, 0.029792, 0.022708, 0.024167, 0.022917],
                            [0.025417, 0.023958, 0.026042, 0.023333, 0.02875],
                            [0.024375, 0.023333, 0.022917, 0.024167, 0.023542],
                            [0.026042, 0.026458, 0.02625, 0.025, 0.027292],
                            [0.021875, 0.026875, 0.02, 0.020625, 0.02312]
                        ],
                        "mesh_params": {
                            "min_x": 10,
                            "max_x": 225,
                            "min_y": 10,
                            "max_y": 225,
                            "x_count": 5,
                            "y_count": 5,
                            "mesh_x_pps": 5,
                            "mesh_y_pps": 5,
                            "algo": "bicubic",
                            "tension": 0.2
                        }
                    },
                }
            },
            "motion_report": {
                "live_position": [
                    0,
                    0,
                    0,
                    0
                ],
                "live_velocity": 0,
                "live_extruder_velocity": 0,
                "steppers": [
                    "extruder",
                    "stepper_x",
                    "stepper_y",
                    "stepper_z"
                ],
                "trapq": [
                    "extruder",
                    "toolhead"
                ]
            },
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

        update = {
            "commandType": MqttMsgType.ZZ_MQTT_CMD_PREHEAT_CONFIG.value,
            "userid": "ankerctl",
            "value": int(bool(pstate.nozzle.target or pstate.hotbed.target)),
            "nozzle": int(pstate.nozzle.target * 100),
            "heatbed": int(pstate.hotbed.target * 100),
        }
        with app.svc.borrow("mqttqueue") as mqttq:
            mqttq.client.command(update)
    else:
        with app.svc.borrow("mqttqueue") as mqttq:
            for line in script.splitlines():
                update = {
                    "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
                    "userid": "ankerctl",
                    "cmdData": line,
                    "cmdLen": len(line),
                }
                mqttq.client.command(update)

    return "ok"
