from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.update.status")
def machine_update_status(refresh=False):
    return {
        "busy": False,
        "github_rate_limit": 60,
        "github_requests_remaining": 57,
        "github_limit_reset_time": 1615836932,
        "version_info": {
            "system": {
                "package_count": 0,
            },
            "ankerctl": {
                "full_version_string": "2.0.0-alpha0",
            },
            "ankermake-m5-linux": {
                "full_version_string": "3.0.16",
            },
            "ankermake-m5-marlin": {
                "full_version_string": "3.0.46",
            },
        }
    }


@dispatcher.add_method(name="machine.update.klipper")
def machine_update_klipper():
    return "ok"


@dispatcher.add_method(name="machine.update.system")
def machine_update_system():
    return "ok"


@dispatcher.add_method(name="machine.update.full")
def machine_update_full():
    return "ok"
