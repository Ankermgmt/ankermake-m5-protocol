import psutil

from flask import current_app as app
from jsonrpc import dispatcher

from libflagship.mqtt import MqttMsgType

from ...lib.gcode import GCode


@dispatcher.add_method(name="printer.print.start")
def printer_print_start(filename):
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
            "fan",
            "heater_fan heater_fan",
            "stepper_enable",
            "controller_fan controller_fan",
            "filament_motion_sensor runout_sensor",
            "output_pin output_pin",
            "pause_resume",
            "display_status",
            "gcode_move",
            "exclude_object",
            "print_stats",
            "virtual_sdcard",
            "firmware_retraction",
            "bed_mesh",
            "motion_report",
            "query_endstops",
            "idle_timeout",
            "system_stats",
            "manual_probe",
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
            "virtual_sdcard": {
                "file_path": None,
                "progress": 0,
                "is_active": True,
                "file_position": 0,
                "file_size": 0
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
                    "printer": {
                        "kinematics": "cartesian",
                        "max_velocity": "300",
                        "max_accel": "3000",
                        "max_z_velocity": "5",
                        "max_z_accel": "100"
                    },
                    "stepper_x": {
                        "step_pin": "PD7",
                        "dir_pin": "!PC5",
                        "enable_pin": "!PD6",
                        "endstop_pin": "^PC2",
                        "microsteps": "16",
                        "rotation_distance": "40",
                        "position_endstop": "0",
                        "position_max": "235",
                        "position_min": "-15",
                        "homing_speed": "50",
                        "homing_retract_dist": "0"
                    },
                    "stepper_y": {
                        "step_pin": "PC6",
                        "dir_pin": "!PC7",
                        "enable_pin": "!PD6",
                        "endstop_pin": "^PC3",
                        "microsteps": "16",
                        "rotation_distance": "40",
                        "position_endstop": "0",
                        "position_max": "235",
                        "position_min": "-15",
                        "homing_speed": "50",
                        "homing_retract_dist": "0"
                    },
                    "stepper_z": {
                        "step_pin": "PB3",
                        "dir_pin": "PB2",
                        "enable_pin": "!PA5",
                        "endstop_pin": "^PC4",
                        "microsteps": "16",
                        "rotation_distance": "8",
                        "position_endstop": "0.0",
                        "position_max": "250",
                        "position_min": "-2",
                        "homing_retract_dist": "0"
                    },
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
                    "extruder": {
                        "step_pin": "PB1",
                        "dir_pin": "!PB0",
                        "enable_pin": "!PD6",
                        "heater_pin": "PD5",
                        "sensor_pin": "PA7",
                        "sensor_type": "EPCOS 100K B57560G104F",
                        "control": "watermark",
                        "microsteps": "16",
                        "rotation_distance": "33.683",
                        "nozzle_diameter": "0.400",
                        "filament_diameter": "1.750",
                        "min_temp": "0",
                        "max_temp": "260",
                        "min_extrude_temp": "50",
                        "max_extrude_only_distance": "50.0",
                        "pressure_advance": "0.1",
                        "pressure_advance_smooth_time": "0.01"
                    },
                    "heater_bed": {
                        "heater_pin": "PD4",
                        "sensor_pin": "PA6",
                        "sensor_type": "EPCOS 100K B57560G104F",
                        "control": "watermark",
                        "min_temp": "0",
                        "max_temp": "130"
                    },
                    "gcode_macro M140": {
                        "rename_existing": "M140.1",
                        "gcode": "\nM117 M140 called with {rawparams}"
                    },
                    "gcode_macro M190": {
                        "rename_existing": "M190.1",
                        "gcode": "\nM117 M190 called with {rawparams}"
                    },
                    "fan": {
                        "pin": "PB4",
                        "off_below": "0.2"
                    },
                    "heater_fan heater_fan": {
                        "pin": "PB5",
                        "off_below": "0.0",
                        "shutdown_speed": "1.0",
                        "max_power": "1.0"
                    },
                    "controller_fan controller_fan": {
                        "pin": "PB6",
                        "off_below": "0.2",
                        "shutdown_speed": "1.0",
                        "max_power": "1.0"
                    },
                    "filament_motion_sensor runout_sensor": {
                        "switch_pin": "PC1",
                        "detection_length": "1.0",
                        "extruder": "extruder",
                        "pause_on_runout": "FALSE",
                        "runout_gcode": "\nM117 Runout sensor reports: Runout G-Code",
                        "insert_gcode": "\nM117 Runout sensor reports: Insert G-Code"
                    },
                    "output_pin output_pin": {
                        "pin": "PC0",
                        "pwm": "false",
                        "shutdown_value": "0",
                        "value": "1"
                    },
                    "respond": {},
                    "pause_resume": {},
                    "display_status": {},
                    "exclude_object": {},
                    "mcu": {
                        "serial": "/tmp/pseudoserial",
                        "restart_method": "arduino"
                    },
                    "virtual_sdcard": {
                        "path": "~/printer_data/gcodes"
                    },
                    "firmware_retraction": {
                        "retract_length": "0.5",
                        "retract_speed": "75",
                        "unretract_speed": "75"
                    },
                    "bed_mesh": {
                        "speed": "120",
                        "horizontal_move_z": "5",
                        "mesh_min": "10, 10",
                        "mesh_max": "225, 225",
                        "probe_count": "5, 5"
                    },
                    "bed_mesh default": {
                        "version": "1",
                        "points": "\n0.075000, 0.069792, 0.062708, 0.044167, 0.032917\n0.045417, 0.043958, 0.066042, 0.053333, 0.038750\n0.034375, 0.023333, 0.032917, 0.054167, 0.043542\n0.076042, 0.056458, 0.066250, 0.045000, 0.057292\n0.051875, 0.036875, 0.030000, 0.020625, 0.043125",
                        "tension": "0.2",
                        "min_x": "10",
                        "algo": "bicubic",
                        "y_count": "5",
                        "mesh_y_pps": "5",
                        "min_y": "10.0",
                        "x_count": "5",
                        "max_y": "225",
                        "mesh_x_pps": "5",
                        "max_x": "225"
                    },
                    "bed_mesh mesh_profile_2": {
                        "version": "1",
                        "points": "\n0.025000, 0.029792, 0.022708, 0.024167, 0.022917\n0.025417, 0.023958, 0.026042, 0.023333, 0.028750\n0.024375, 0.023333, 0.022917, 0.024167, 0.023542\n0.026042, 0.026458, 0.026250, 0.025000, 0.027292\n0.021875, 0.026875, 0.020000, 0.020625, 0.023125",
                        "tension": "0.2",
                        "min_x": "10",
                        "algo": "bicubic",
                        "y_count": "5",
                        "mesh_y_pps": "5",
                        "min_y": "10.0",
                        "x_count": "5",
                        "max_y": "225",
                        "mesh_x_pps": "5",
                        "max_x": "225"
                    },
                },
                "settings": {
                    "mcu": {
                        "serial": "/tmp/pseudoserial",
                        "baud": 250000,
                        "restart_method": "arduino",
                        "max_stepper_error": 0.000025
                    },
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
                    "heater_bed": {
                        "sensor_type": "EPCOS 100K B57560G104F",
                        "pullup_resistor": 4700,
                        "inline_resistor": 0,
                        "sensor_pin": "PA6",
                        "min_temp": 0,
                        "max_temp": 130,
                        "min_extrude_temp": 170,
                        "max_power": 1,
                        "smooth_time": 1,
                        "control": "watermark",
                        "max_delta": 2,
                        "heater_pin": "PD4",
                        "pwm_cycle_time": 0.1
                    },
                    "verify_heater heater_bed": {
                        "hysteresis": 5,
                        "max_error": 120,
                        "heating_gain": 2,
                        "check_gain_time": 60
                    },
                    "gcode_macro m140": {
                        "gcode": "\nM117 M140 called with {rawparams}",
                        "rename_existing": "M140.1",
                        "description": "G-Code macro"
                    },
                    "gcode_macro m190": {
                        "gcode": "\nM117 M190 called with {rawparams}",
                        "rename_existing": "M190.1",
                        "description": "G-Code macro"
                    },
                    "fan": {
                        "max_power": 1,
                        "kick_start_time": 0.1,
                        "off_below": 0.2,
                        "cycle_time": 0.01,
                        "hardware_pwm": False,
                        "shutdown_speed": 0,
                        "pin": "PB4"
                    },
                    "heater_fan heater_fan": {
                        "heater": [
                            "extruder"
                        ],
                        "heater_temp": 50,
                        "max_power": 1,
                        "kick_start_time": 0.1,
                        "off_below": 0,
                        "cycle_time": 0.01,
                        "hardware_pwm": False,
                        "shutdown_speed": 1,
                        "pin": "PB5",
                        "fan_speed": 1
                    },
                    "controller_fan controller_fan": {
                        "max_power": 1,
                        "kick_start_time": 0.1,
                        "off_below": 0.2,
                        "cycle_time": 0.01,
                        "hardware_pwm": False,
                        "shutdown_speed": 1,
                        "pin": "PB6",
                        "fan_speed": 1,
                        "idle_speed": 1,
                        "idle_timeout": 30,
                        "heater": [
                            "extruder"
                        ]
                    },
                    "filament_motion_sensor runout_sensor": {
                        "switch_pin": "PC1",
                        "extruder": "extruder",
                        "detection_length": 1,
                        "pause_on_runout": False,
                        "runout_gcode": "\nM117 Runout sensor reports: Runout G-Code",
                        "insert_gcode": "\nM117 Runout sensor reports: Insert G-Code",
                        "pause_delay": 0.5,
                        "event_delay": 3
                    },
                    "output_pin output_pin": {
                        "pwm": False,
                        "pin": "PC0",
                        "maximum_mcu_duration": 0,
                        "value": 1,
                        "shutdown_value": 0
                    },
                    "respond": {
                        "default_type": "echo",
                        "default_prefix": "echo:"
                    },
                    "pause_resume": {
                        "recover_velocity": 50
                    },
                    "virtual_sdcard": {
                        "path": "~/printer_data/gcodes",
                        "on_error_gcode": ""
                    },
                    "firmware_retraction": {
                        "retract_length": 0.5,
                        "retract_speed": 75,
                        "unretract_extra_length": 0,
                        "unretract_speed": 75
                    },
                    "bed_mesh": {
                        "probe_count": [
                            5,
                            5
                        ],
                        "mesh_min": [
                            10,
                            10
                        ],
                        "mesh_max": [
                            225,
                            225
                        ],
                        "mesh_pps": [
                            2,
                            2
                        ],
                        "algorithm": "lagrange",
                        "bicubic_tension": 0.2,
                        "horizontal_move_z": 5,
                        "speed": 120,
                        "fade_start": 1,
                        "fade_end": 0,
                        "split_delta_z": 0.025,
                        "move_check_distance": 5
                    },
                    "bed_mesh default": {
                        "version": 1,
                        "points": [
                            [
                                0.075,
                                0.069792,
                                0.062708,
                                0.044167,
                                0.032917
                            ],
                            [
                                0.045417,
                                0.043958,
                                0.066042,
                                0.053333,
                                0.03875
                            ],
                            [
                                0.034375,
                                0.023333,
                                0.032917,
                                0.054167,
                                0.043542
                            ],
                            [
                                0.076042,
                                0.056458,
                                0.06625,
                                0.045,
                                0.057292
                            ],
                            [
                                0.051875,
                                0.036875,
                                0.03,
                                0.020625,
                                0.043125
                            ]
                        ],
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
                    },
                    "bed_mesh mesh_profile_2": {
                        "version": 1,
                        "points": [
                            [ 0.025, 0.029792, 0.022708, 0.024167, 0.022917 ],
                            [ 0.025417, 0.023958, 0.026042, 0.023333, 0.02875 ],
                            [ 0.024375, 0.023333, 0.022917, 0.024167, 0.023542 ],
                            [ 0.026042, 0.026458, 0.02625, 0.025, 0.027292 ],
                            [ 0.021875, 0.026875, 0.02, 0.020625, 0.023125 ]
                        ],
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
                    },
                    "bed_mesh mesh_profile_3": {
                        "version": 1,
                        "points": [
                            [0.075, 0.069792, 0.062708, 0.044167, -0.032917],
                            [0.045417, 0.043958, 0.066042, -0.053333, -0.03875],
                            [0.034375, 0.023333, -0.032917, -0.054167, -0.043542],
                            [0.076042, -0.056458, -0.06625, -0.045, -0.057292],
                            [-0.051875, -0.036875, -0.03, -0.020625, -0.043125]
                        ],
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
                    },
                    "printer": {
                        "max_velocity": 300,
                        "max_accel": 3000,
                        "max_accel_to_decel": 1500,
                        "square_corner_velocity": 5,
                        "buffer_time_low": 1,
                        "buffer_time_high": 2,
                        "buffer_time_start": 0.25,
                        "move_flush_time": 0.05,
                        "kinematics": "cartesian",
                        "max_z_velocity": 5,
                        "max_z_accel": 100
                    },
                    "stepper_x": {
                        "step_pin": "PD7",
                        "dir_pin": "!PC5",
                        "rotation_distance": 40,
                        "microsteps": 16,
                        "full_steps_per_rotation": 200,
                        "gear_ratio": [],
                        "enable_pin": "!PD6",
                        "endstop_pin": "^PC2",
                        "position_endstop": 0,
                        "position_min": -15,
                        "position_max": 235,
                        "homing_speed": 50,
                        "second_homing_speed": 25,
                        "homing_retract_speed": 50,
                        "homing_retract_dist": 0,
                        "homing_positive_dir": False
                    },
                    "force_move": {
                        "enable_force_move": False
                    },
                    "stepper_y": {
                        "step_pin": "PC6",
                        "dir_pin": "!PC7",
                        "rotation_distance": 40,
                        "microsteps": 16,
                        "full_steps_per_rotation": 200,
                        "gear_ratio": [],
                        "enable_pin": "!PD6",
                        "endstop_pin": "^PC3",
                        "position_endstop": 0,
                        "position_min": -15,
                        "position_max": 235,
                        "homing_speed": 50,
                        "second_homing_speed": 25,
                        "homing_retract_speed": 50,
                        "homing_retract_dist": 0,
                        "homing_positive_dir": False
                    },
                    "stepper_z": {
                        "step_pin": "PB3",
                        "dir_pin": "PB2",
                        "rotation_distance": 8,
                        "microsteps": 16,
                        "full_steps_per_rotation": 200,
                        "gear_ratio": [],
                        "enable_pin": "!PA5",
                        "endstop_pin": "^PC4",
                        "position_endstop": 0,
                        "position_min": -2,
                        "position_max": 250,
                        "homing_speed": 5,
                        "second_homing_speed": 2.5,
                        "homing_retract_speed": 5,
                        "homing_retract_dist": 0,
                        "homing_positive_dir": False
                    },
                    "idle_timeout": {
                        "timeout": 600,
                        "gcode": "\n{% if 'heaters' in printer %}\n   TURN_OFF_HEATERS\n{% endif %}\nM84\n"
                    },
                    "extruder": {
                        "sensor_type": "EPCOS 100K B57560G104F",
                        "pullup_resistor": 4700,
                        "inline_resistor": 0,
                        "sensor_pin": "PA7",
                        "min_temp": 0,
                        "max_temp": 260,
                        "min_extrude_temp": 50,
                        "max_power": 1,
                        "smooth_time": 1,
                        "control": "watermark",
                        "max_delta": 2,
                        "heater_pin": "PD5",
                        "pwm_cycle_time": 0.1,
                        "nozzle_diameter": 0.4,
                        "filament_diameter": 1.75,
                        "max_extrude_cross_section": 0.6400000000000001,
                        "max_extrude_only_velocity": 79.82432411074329,
                        "max_extrude_only_accel": 798.2432411074329,
                        "max_extrude_only_distance": 50,
                        "instantaneous_corner_velocity": 1,
                        "step_pin": "PB1",
                        "pressure_advance": 0.1,
                        "pressure_advance_smooth_time": 0.01,
                        "dir_pin": "!PB0",
                        "rotation_distance": 33.683,
                        "microsteps": 16,
                        "full_steps_per_rotation": 200,
                        "gear_ratio": [],
                        "enable_pin": "!PD6"
                    },
                    "verify_heater extruder": {
                        "hysteresis": 5,
                        "max_error": 120,
                        "heating_gain": 2,
                        "check_gain_time": 20
                    }
                },
                "warnings": [],
                "save_config_pending": False,
                "save_config_pending_items": {}
            },
            "mcu": {
                "mcu_version": "Linux 4.4.94",
                "mcu_build_versions": "Ingenic r4.1.1-gcc720-glibc226-fp64 2020.11-05",
                "mcu_constants": {
                    "ADC_MAX": 1023,
                    "BUS_PINS_spi": "PB6,PB5,PB7",
                    "BUS_PINS_twi": "PC0,PC1",
                    "CLOCK_FREQ": 20000000,
                    "MCU": "Ingenic XBurst@II.V2",
                    "PWM_MAX": 255,
                    "RECEIVE_WINDOW": 192,
                    "RESERVE_PINS_serial": "PD0,PD1",
                    "SERIAL_BAUD": 10000000,
                    "STATS_SUMSQ_BASE": 256
                },
                "last_stats": {
                    "mcu_awake": 0.011,
                    "mcu_task_avg": 0.00008,
                    "mcu_task_stddev": 0.00005,
                    "bytes_write": 10696,
                    "bytes_read": 45413,
                    "bytes_retransmit": 9,
                    "bytes_invalid": 0,
                    "send_seq": 1726,
                    "receive_seq": 1726,
                    "retransmit_seq": 17,
                    "srtt": 0.01,
                    "rttvar": 0.001,
                    "rto": 0.025,
                    "ready_bytes": 0,
                    "upcoming_bytes": 0,
                    "freq": 2054046
                }
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
            "filament_motion_sensor runout_sensor": {
                "filament_detected": True,
                "enabled": True
            },
            "output_pin output_pin": {
                "value": 1
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
            "firmware_retraction": {
                "retract_length": 0.5,
                "retract_speed": 75,
                "unretract_extra_length": 0,
                "unretract_speed": 75
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
            "query_endstops": {
                "last_query": {}
            },
            "system_stats": {
                "sysload": psutil.getloadavg()[0],
                "cputime": psutil.cpu_times().user,
                "memavail": psutil.virtual_memory().available,
            },
            "manual_probe": {
                "is_active": False,
                "z_position": None,
                "z_position_lower": None,
                "z_position_upper": None
            }
        }
    }


@dispatcher.add_method(name="printer.query_endstops.status")
def printer_query_endstops_status():
    return {
        "x": "TRIGGERED",
        "y": "open",
        "z": "open"
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

        if gcode.vals["HEATER"] == "extruder":
            pstate.nozzle.target = float(gcode.vals["TARGET"])
        elif gcode.vals["HEATER"] == "heater_bed":
            pstate.hotbed.target = float(gcode.vals["TARGET"])

        update = {
            "commandType": MqttMsgType.ZZ_MQTT_CMD_PREHEAT_CONFIG.value,
            "userid": "ankerctl",
            "value": int(bool(pstate.nozzle.target or pstate.hotbed.target)),
            "nozzle": int(pstate.nozzle.target * 100),
            "heatbed": int(pstate.hotbed.target * 100),
        }
    else:
        update = {
            "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
            "cmdData": script,
            "cmdLen": len(script),
        }

    with app.svc.borrow("mqttqueue") as mqttq:
        mqttq.client.command(update)

    return "ok"
