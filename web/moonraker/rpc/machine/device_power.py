from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.device_power.devices")
def machine_device_power_devices():
    return {
        "devices": []
    }


@dispatcher.add_method(name="machine.device_power.on")
def machine_device_power_on(**objs):
    return "ok"
