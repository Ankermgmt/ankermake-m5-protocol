from jsonrpc import dispatcher


@dispatcher.add_method(name="machine.timelapse.get_settings")
def machine_timelapse_get_settings():
    return {
        "blockedsettings": [],
        "snapshoturl": "",
        "rotation": 0,
        "flip_x": False,
        "flip_y": False,
    }


@dispatcher.add_method(name="machine.timelapse.post_settings")
def machine_timelapse_post_settings(**kwargs):
    raise NotImplementedError()


@dispatcher.add_method(name="machine.timelapse.render")
def machine_timelapse_render():
    raise NotImplementedError()


@dispatcher.add_method(name="machine.timelapse.saveframes")
def machine_timelapse_saveframes():
    return {
        "status": "finished",
        "msg": "",
    }


@dispatcher.add_method(name="machine.timelapse.lastframeinfo")
def machine_timelapse_lastframeinfo():
    return {
         "framecount": 0,
         "lastframefile": ""
    }
