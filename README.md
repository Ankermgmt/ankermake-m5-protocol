# Ankermake M5 Protocol

Welcome! This repository contains `ankerctl.py`, a command-line interface for
monitoring, controlling and interfacing with Ankermake M5 3D printers.

NOTE: This software is in early stages, so expect sharp edges and occasional errors!

The `ankerctl` program uses [`libflagship`](documentation/libflagship.md), a
library for communicating with the numerous different protocols required for
connecting to an Ankermake M5 printer. The `libflagship` library is also maintained
in this repo, under [`libflagship/`](libflagship/).

## Current features

 - Print directly from PrusaSlicer, SuperSlicer

 - Connect to Ankermake M5 and Ankermake APIs without using closed-source Anker
   software.

 - Send raw gcode commands directly to the printer (and see the response)

 - Low-level access to MQTT, PPPP and HTTPS APIs

 - Send print jobs to the printer

 - Stream camera image/video to your computer


## Upcoming and planned features

 - Easily monitor print status

 - Integration into other software. Home Assistant? Prusa Slicer?

Pull requests always welcome :-)

## Installation instructions

First, please follow the [installation
instructions](documentation/example-file-usage/example-file-prerequistes.md) for
your platform.

Verify that you can start `ankerctl.py`, and get the help screen:

### For Windows, use: 
```powershell
python3 ankerctl.py -h
```
If that does not work then try running using `python ankerctl.py -h`

### Linux and MacOS, use:
```sh
./ankerctl.py -h
```

You should see the below output - if not then head back to [installation instructions](documentation/example-file-usage/example-file-prerequistes.md)
```
Usage: ankerctl.py [OPTIONS] COMMAND [ARGS]...

Options:
  -k, --insecure  Disable TLS certificate validation
  -v, --verbose   Increase verbosity
  -q, --quiet     Decrease verbosity
  -h, --help      Show this message and exit.

Commands:
  config  View and update configuration
  http    Low-level http api access
  mqtt    Low-level mqtt api access
  pppp    Low-level pppp api access
```

Before you can use ankerctl, you need to import the configuration.

Support for logging in with username and password is not yet supported, but an
`auth_token` can be imported from the saved credentials found in `login.json` in
Ankermake Slicer. See `ankerctl.py config import -h` for details:

```
Usage: ankerctl.py config import [OPTIONS] path/to/login.json

  Import printer and account information from login.json

  When run without filename, attempt to auto-detect login.json in default
  install location

Options:
  -h, --help  Show this message and exit.
```

On Windows and MacOS, the default location of `login.json` will be tried if no
filename is specified. Otherwise, you can specify the file path for
`login.json`. Example for linux:

```sh
ankerctl.py config import ~/.wine/drive_c/users/username/AppData/Local/AnkerMake/AnkerMake_64bit_fp/login.json
```

The expected output is similar to this:
```
[*] Loading cache..
[*] Initializing API..
[*] Requesting profile data..
[*] Requesting printer list..
[*] Requesting pppp keys..
[*] Adding printer [AK7ABC0123401234]
[*] Finished import
```

At this point, your config is saved to a configuration file managed by
`ankerctl.py`. To see an overview of the stored data, use `config show`:

```sh
./ankerctl.py config show
[*] Account:
    user_id: 01234567890abcdef012...<REDACTED>
    email:   bob@example.org
    region:  eu

[*] Printers:
    sn: AK7ABC0123401234
    duid: EUPRAKM-001234-ABCDE
```

NOTE: The cached login info contains sensitive details. In particular, the
`user_id` field is used when connecting to MQTT servers, and essentially works
as a password. Thus, the end of the value is redacted when printed to screen, to avoid
accidentally disclosing sensitive information.

Now that the printer information is known to `ankerctl`, the tool is ready to use.

Some examples:

```sh
# attempt to detect printers on local network
./ankerctl.py pppp lan-search

# monitor mqtt events
./ankerctl.py mqtt monitor

# start gcode prompt
./ankerctl.py mqtt gcode

# set printer name
./ankerctl.py mqtt rename-printer BoatyMcBoatFace

# print boaty.gcode
./ankerctl.py pppp print-file boaty.gcode

# capture 4mb of video from camera
./ankerctl.py pppp capture-video -m 4mb output.h264
```

## Webserver

ankerctl can also be used as a webserver to allow slicers like prusaslicer to print directly to the printer. 

![Screenshot of prusa slicer](/static/img/setup/prusaslicer-2.png?raw=true "Screenshot of prusa slicer")

To start the webserver run the following command, then navigate to [http://localhost:4470](http://localhost:4470)

```sh
./ankerctl.py webserver run
```

You can alternativly use docker compose to start the webserver running behind nginx

```sh
docker compose up
```



## Docker

While running the python script is generally prefered, there may be situations where you want a more portable solution. For this, a docker image is provided.

```sh
docker build -t ankerctl .
```

Example usage (no peristent storage)
```bash
docker run \
  -v "$HOME/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json:/tmp/login.json" \
  ankerctl config decode /tmp/login.json
```

Example usage (with peristent storage)
```bash
# create volume where we can store configs
docker volume create ankerctl_vol

# generate /root/.config/ankerctl/default.json which is mounted to the docker volume
docker run \
  -v ankerctl_vol:/root/.config/ankerctl \
  -v "$HOME/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json:/tmp/login.json" \
  ankerctl config import /tmp/login.json

# Now that there is a /root/.config/ankerctl/default.json file that persists in the docker volume
# we can run ankerctl without having to specify the login.json file
docker run \
  -v ankerctl_vol:/root/.config/ankerctl \
  ankerctl config show
```


## Legal

This project is in ABSOLUTELY NO WAY endorsed, affiliated with, or supported by
Anker. All information found herein is gathered entirely from reverse
engineering.

The goal of this project is to make the Ankermake M5 usable and accessible using
only Free and Open Source Software.

This project is [licensed under the GNU GPLv3](LICENSE), and copyright © 2023
Christian Iversen.
