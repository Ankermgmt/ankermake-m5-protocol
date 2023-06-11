from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.device_power.devices")
def machine_device_power_devices():
    return {
        "devices": []
    }


@dispatcher.add_method(name="machine.device_power.on")
def machine_device_power_on(**objs):
    return "ok"


@dispatcher.add_method(name="machine.device_power.post_device")
def machine_device_power_power_device(**objs):
    raise NotImplementedError()
