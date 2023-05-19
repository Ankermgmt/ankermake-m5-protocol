# AnkerMake M5 Protocol

Welcome! This repository contains `ankerctl.py`, a command-line interface for monitoring, controlling and interfacing with AnkerMake M5 3D printers.

**NOTE:** This software is in early stages, so expect sharp edges and occasional errors!

The `ankerctl` program uses [`libflagship`](documentation/libflagship.md), a library for communicating with the numerous different protocols required for connecting to an AnkerMake M5 printer. The `libflagship` library is also maintained in this repo, under [`libflagship/`](libflagship/).

## Features

### Current Features

 - Print directly from PrusaSlicer and its derivatives (SuperSlicer, Bamboo Studio, OrcaSlicer, etc.)

 - Connect to AnkerMake M5 and AnkerMake APIs without using closed-source Anker software.

 - Send raw gcode commands directly to the printer (and see the response).

 - Low-level access to MQTT, PPPP and HTTPS APIs.

 - Send print jobs (gcode files) to the printer.

 - Stream camera image/video to your computer.

### Upcoming and Planned Features

 - Easily monitor print status.

 - Integration into other software. Home Assistant? Cura plugin?

Let us know what you want to see; Pull requests always welcome! :smile:

## Installation (Prerequisite to the Usage section)

Follow the instructions for a [docker install](./documentation/install-from-docker.md) (recommended) or a [git install](./documentation/install-from-git.md).

## Usage

### Web Interface

1. Start the webserver by running one of the following commands in the folder you placed ankerctl in. You’ll need to have this running whenever you want to use the web interface or send jobs to the printer via a slicer:

   docker:

   ```sh
   docker compose up
   ```

   python:

   ```sh
   ./ankerctl.py webserver run
   ```

2. Navigate to [http://localhost:4470](http://localhost:4470) in your browser of choice on the same computer the webserver is running on. You’ll be prompted to upload your `login.json` file and the given the default path it should be found in your corresponding Operating System. Once the `login.json` has been uploaded, the page will refresh and the web interface is usable. To access it from other devices (must be on the same network), replace “localhost” with the IP address of the computer running the web server.

### CLI Utilities (Python Scripts)

1. Import your AnkerMake account data by opening a terminal window in the folder you placed ankerctl in and running the following command:

   ```sh
   ankerctl.py config import [OPTIONS] path/to/login.json 
   ```

   When run without filename on Windows and MacOS, the default location of `login.json` will be tried if no filename is specified. Otherwise, you can specify the file path for `login.json`. Example for Linux:
   ```sh
   ankerctl.py config import ~/.wine/drive_c/users/username/AppData/Local/AnkerMake/AnkerMake_64bit_fp/login.json
   ```
   MacOS
   ```sh
   ./ankerctl.py config import $HOME/Library/Application\ Support/AnkerMake/AnkerMake_64bit_fp/login.json
   ```
   Windows
   ```sh
   python3 ankerctl.py config import %APPDATA%\AnkerMake\AnkerMake_64bit_fp\login.json
   ```

   Type `ankerctl.py config import -h` for more details on the import options. Support for logging in with username and password is not yet supported. To learn more about the method used to extract the login information and add printers, see the [MQTT Overview](./documentation/mqtt-overview.md) and [Example Files](./documentation/example-file-usage) documentation.

   The output when successfully importing a config is similar to this:

   ```
   [*] Loading cache..
   [*] Initializing API..
   [*] Requesting profile data..
   [*] Requesting printer list..
   [*] Requesting pppp keys..
   [*] Adding printer [AK7ABC0123401234]
   [*] Finished import
   ```

   At this point, your config is saved to a configuration file managed by `ankerctl.py`. To see an overview of the stored data, use `config show`:

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

   **NOTE:** The cached login info contains sensitive details. In particular, the `user_id` field is used when connecting to MQTT servers, and essentially works as a password. Thus, the end of the value is redacted when printed to screen, to avoid accidentally disclosing sensitive information.

2. Now that the printer information is known to `ankerctl`, the tool is ready to use. There’s a lot of available commands and utilities, use a command followed by `-h` to learn what your options are and get more in specific usage instructions.

Some examples:

```
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

# select printer to use when you have multiple
./ankerctl.py -p <index> #index starts at 0 and goes up to the number of printers you have
```

### Printing Directly from PrusaSlicer

ankerctl can allow slicers like PrusaSlicer (and its derivatives) to send print jobs directly to the printer using the slicer’s built in communications tools. The web server must be running in order to send jobs to the printer. Currently there’s no way to store the jobs for later printing on the printer, so you’re limited to using the “Send and Print” option only to immediately start the print once it’s been transmitted. Additional instructions can be found in the web interface.

![Screenshot of prusa slicer](/static/img/setup/prusaslicer-2.png "Screenshot of prusa slicer")

## Legal

This project is **<u>NOT</u>** endorsed, affiliated with, or supported by AnkerMake. All information found herein is gathered entirely from reverse engineering using publicly available knowledge and resources.

The goal of this project is to make the AnkerMake M5 usable and accessible using only Free and Open Source Software (FOSS).

This project is [licensed under the GNU GPLv3](LICENSE), and copyright © 2023 Christian Iversen.
