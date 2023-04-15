from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.update.status")
def machine_update_status(**kwargs):
    return {
        "busy": False,
        "github_rate_limit": 60,
        "github_requests_remaining": 57,
        "github_limit_reset_time": 1615836932,
        "version_info": {
            "ankerctl": {
                "full_version_string": "0.1.2.3",
            },
            "libflagship": {
                "full_version_string": "0.4.5.6",
            },
            # "system": {
            #     "package_count": 4,
            #     "package_list": [
            #         "libtiff5",
            #         "raspberrypi-sys-mods",
            #         "rpi-eeprom-images",
            #         "rpi-eeprom"
            #     ]
            # },
            # "moonraker": {
            #     "channel": "dev",
            #     "debug_enabled": True,
            #     "need_channel_update": False,
            #     "is_valid": True,
            #     "configured_type": "git_repo",
            #     "corrupt": False,
            #     "info_tags": [],
            #     "detected_type": "git_repo",
            #     "remote_alias": "arksine",
            #     "branch": "master",
            #     "owner": "?",
            #     "repo_name": "moonraker",
            #     "version": "v0.7.1-364",
            #     "remote_version": "v0.7.1-364",
            #     "current_hash": "ecfad5cff15fff1d82cb9bdc64d6b548ed53dfaf",
            #     "remote_hash": "ecfad5cff15fff1d82cb9bdc64d6b548ed53dfaf",
            #     "is_dirty": False,
            #     "detached": True,
            #     "commits_behind": [],
            #     "git_messages": [],
            #     "full_version_string": "v0.7.1-364-gecfad5c",
            #     "pristine": True
            # },
            # "mainsail": {
            #     "name": "mainsail",
            #     "owner": "mainsail-crew",
            #     "version": "v2.1.1",
            #     "remote_version": "v2.1.1",
            #     "configured_type": "web",
            #     "channel": "stable",
            #     "info_tags": [
            #         "desc=Mainsail Web Client",
            #         "action=some_action"
            #     ]
            # },
            # "fluidd": {
            #     "name": "fluidd",
            #     "owner": "cadriel",
            #     "version": "?",
            #     "remote_version": "v1.16.2",
            #     "configured_type": "web_beta",
            #     "channel": "beta",
            #     "info_tags": []
            # },
            # "klipper": {
            #     "channel": "dev",
            #     "debug_enabled": True,
            #     "need_channel_update": False,
            #     "is_valid": True,
            #     "configured_type": "git_repo",
            #     "corrupt": False,
            #     "info_tags": [],
            #     "detected_type": "git_repo",
            #     "remote_alias": "origin",
            #     "branch": "master",
            #     "owner": "Klipper3d",
            #     "repo_name": "klipper",
            #     "version": "v0.12.0-1",
            #     "remote_version": "v0.12.0-41",
            #     "current_hash": "4c8d24ae03eadf3fc5a28efb1209ce810251d02d",
            #     "remote_hash": "e3cbe7ea3663a8cd10207a9aecc4e5458aeb1f1f",
            #     "is_dirty": False,
            #     "detached": False,
            #     "commits_behind": [
            #         {
            #             "sha": "e3cbe7ea3663a8cd10207a9aecc4e5458aeb1f1f",
            #             "author": "Kevin O'Connor",
            #             "date": "1644534721",
            #             "subject": "stm32: Clear SPE flag on a change to SPI CR1 register",
            #             "message": "The stm32 specs indicate that the SPE bit must be cleared before\nchanging the CPHA or CPOL bits.\n\nReported by @cbc02009 and @bigtreetech.\n\nSigned-off-by: Kevin O'Connor <kevin@koconnor.net>",
            #             "tag": None
            #         },
            #         {
            #             "sha": "99d55185a21703611b862f6ce4b80bba70a9c4b5",
            #             "author": "Kevin O'Connor",
            #             "date": "1644532075",
            #             "subject": "stm32: Wait for transmission to complete before returning from spi_transfer()",
            #             "message": "It's possible for the SCLK pin to still be updating even after the\nlast byte of data has been read from the receive pin.  (In particular\nin spi mode 0 and 1.)  Exiting early from spi_transfer() in this case\ncould result in the CS pin being raised before the final updates to\nSCLK pin.\n\nAdd an additional wait at the end of spi_transfer() to avoid this\nissue.\n\nSigned-off-by: Kevin O'Connor <kevin@koconnor.net>",
            #             "tag": None
            #         },
            #     ],
            #     "git_messages": [],
            #     "full_version_string": "v0.12.0-1-g4c8d24ae-shallow",
            #     "pristine": True
            # }
        }
    }


@dispatcher.add_method(name="machine.device_power.devices")
def machine_device_power_devices(**kwargs):
    return {
        "devices": [
            {
                "device": "green_led",
                "status": "off",
                "locked_while_printing": True,
                "type": "gpio"
            },
            {
                "device": "printer",
                "status": "off",
                "locked_while_printing": False,
                "type": "tplink_smartplug"
            }
        ]
    }


@dispatcher.add_method(name="machine.proc_stats")
def machine_proc_stats(**kwargs):
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
        "cpu_temp": 45.622,
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
        "websocket_connections": 4
    }
