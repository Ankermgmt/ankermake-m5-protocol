# AnkerMake M5 Protocol

Welcome! This repository contains `ankerctl`, a command-line interface and web UI for monitoring, controlling and interfacing with AnkerMake M5 and M5C 3D printers.

**NOTE:** This is our first major release and while we have tested thoroughly there may be bugs. If you encounter one please open a [Github Issue](https://github.com/Ankermgmt/ankermake-m5-protocol/issues/new/choose)

The `ankerctl` program uses [`libflagship`](documentation/developer-docs/libflagship.md), a library for communicating with the numerous different protocols required for connecting to an AnkerMake M5 or M5C printer. The `libflagship` library is also maintained in this repo, under [`libflagship/`](libflagship/).

![Screenshot of ankerctl](/documentation/web-interface.png "Screenshot of ankerctl web interface")

## Features

### Current Features

 - Print directly from PrusaSlicer and its derivatives (SuperSlicer, Bamboo Studio, OrcaSlicer, etc.)

 - Connect to AnkerMake M5/M5C and AnkerMake APIs without using closed-source Anker software.

 - Send raw gcode commands to the printer (and see the response).

 - Low-level access to MQTT, PPPP and HTTPS APIs.

 - Send print jobs (gcode files) to the printer.

 - Stream camera image/video to your computer (AnkerMake M5 only).

 - Easily monitor print status.

### Upcoming and Planned Features

 - Integration into other software. Home Assistant? Cura plugin?

Let us know what you want to see; Pull requests always welcome! :smile:

## Installation

There are currently two ways to do an install of ankerctl. You can install directly from git utilizing python on your Operating System or you can install from Docker which will install ankerctl in a containerized environment. Only one installation method should be chosen. 

Order of Operations for Success:
- Choose installation method: [Docker](documentation/install-from-docker.md) or [Git](documentation/install-from-git.md)
- Follow the installation intructions for the install method
- Import the login.json file
- Have fun! Either run `ankerctl` from CLI or launch the webserver

> **Note**
> Minimum version of Python required is 3.10

> **Warning**
> Docker Installation ONLY works on Linux at this time

Follow the instructions for a [git install](documentation/install-from-git.md) (recommended), or [docker install](documentation/install-from-docker.md).

## Importing configuration

1. Import your AnkerMake account data by opening a terminal window in the folder you placed ankerctl in and running the following command:

   ```sh
   python3 ankerctl.py config import
   ```

   When run without filename on Windows and MacOS, the default location of `login.json` will be tried if no filename is specified.

   Otherwise, you can specify the file path for `login.json`. Example for Linux:
   ```sh
   ./ankerctl.py config import ~/.wine/drive_c/users/username/AppData/Local/AnkerMake/AnkerMake_64bit_fp/login.json
   ```
   MacOS
   ```sh
   ./ankerctl.py config import $HOME/Library/Application\ Support/AnkerMake/AnkerMake_64bit_fp/login.json
   ```
   Windows
   ```sh
   python3 ankerctl.py config import %APPDATA%\AnkerMake\AnkerMake_64bit_fp\login.json
   ```

   Type `ankerctl.py config import -h` for more details on the import options. Support for logging in with username and password is not yet supported. To learn more about the method used to extract the login information and add printers, see the [MQTT Overview](documentation/developer-docs/mqtt-overview.md) and [Example Files](documentation/developer-docs/example-file-usage) documentation.

   The output when successfully importing a config is similar to this:

   ```sh
   [*] Loading cache..
   [*] Initializing API..
   [*] Requesting profile data..
   [*] Requesting printer list..
   [*] Requesting pppp keys..
   [*] Adding printer [AK7ABC0123401234]
   [*] Finished import
   ```

   At this point, your config is saved to a configuration file managed by `ankerctl`. To see an overview of the stored data, use `config show`:

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

> **NOTE:** 
> The cached login info contains sensitive details. In particular, the `user_id` field is used when connecting to MQTT servers, and essentially works as a password. Thus, the end of the value is redacted when printed to screen, to avoid accidentally disclosing sensitive information.

2. Now that the printer information is known to `ankerctl`, the tool is ready to use. There’s a lot of available commands and utilities, use a command followed by `-h` to learn what your options are and get more in specific usage instructions.

> **NOTE:**
> As an alternative to using "config import" on the command line, it is possible to upload `login.json` through the web interface. Either method will work fine.

## Usage

### Web Interface

1. Start the webserver by running one of the following commands in the folder you placed ankerctl in. You’ll need to have this running whenever you want to use the web interface or send jobs to the printer via a slicer:

   Docker Installation Method:

   ```sh
   docker compose up
   ```

   Git Installation Method Using Python:

   ```sh
   ./ankerctl.py webserver run
   ```

2. Navigate to [http://localhost:4470](http://localhost:4470) in your browser of choice on the same computer the webserver is running on. 
 
 > **Important**
 > If your `login.json` file was not automatically found, you’ll be prompted to upload your `login.json` file and the given the default path it should be found in your corresponding Operating System. 
   Once the `login.json` has been uploaded, the page will refresh and the web interface is usable.

### Printing Directly from PrusaSlicer

ankerctl can allow slicers like PrusaSlicer (and its derivatives) to send print jobs to the printer using the slicer’s built in communications tools. The web server must be running in order to send jobs to the printer. 

Currently there’s no way to store the jobs for later printing on the printer, so you’re limited to using the “Send and Print” option only to immediately start the print once it’s been transmitted. 

Additional instructions can be found in the web interface.

![Screenshot of prusa slicer](/static/img/setup/prusaslicer-2.png "Screenshot of prusa slicer")

### Command-line tools

Some examples:

```sh
# run the webserver to control over webgui
./ankerctl.py webserver run

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
./ankerctl.py -p <index> # index starts at 0 and goes up to the number of printers you have
```

## Legal

This project is **<u>NOT</u>** endorsed, affiliated with, or supported by AnkerMake. All information found herein is gathered entirely from reverse engineering using publicly available knowledge and resources.

The goal of this project is to make the AnkerMake M5 and M5C usable and accessible using only Free and Open Source Software (FOSS).

This project is [licensed under the GNU GPLv3](LICENSE), and copyright © 2023 Christian Iversen.

Some icons from [IconFinder](https://www.iconfinder.com/iconsets/3d-printing-line), and licensed under [Creative Commons](https://creativecommons.org/licenses/by/3.0/)
