# AnkerMake M5 Protocol

Welcome! This repository contains `ankerctl`, a command-line interface and web UI for monitoring, controlling and interfacing with AnkerMake M5 3D printers.

**NOTE:** This is our first major release and while we have tested thoroughly there may be bugs. If you encounter one please open a [Github Issue](https://github.com/Ankermgmt/ankermake-m5-protocol/issues/new/choose)

The `ankerctl` program uses [`libflagship`](documentation/developer-docs/libflagship.md), a library for communicating with the numerous different protocols required for connecting to an AnkerMake M5 printer. The `libflagship` library is also maintained in this repo, under [`libflagship/`](libflagship/).

![Screenshot of ankerctl](/documentation/web-interface.png "Screenshot of ankerctl web interface")

## Features

### Current Features

 - Print directly from PrusaSlicer and its derivatives (SuperSlicer, Bamboo Studio, OrcaSlicer, etc.)

 - Connect to AnkerMake M5 and AnkerMake APIs without using closed-source Anker software.

 - Send raw gcode commands to the printer (and see the response).

 - Low-level access to MQTT, PPPP and HTTPS APIs.

 - Send print jobs (gcode files) to the printer.

 - Stream camera image/video to your computer.

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

   When run without filename on Windows and MacOS, the default location of `login.json` (or `user_info` on Windows) will be tried if no filename is specified.

   Otherwise, you can specify the file path for `login.json`. Example for Linux:
   ```sh
   ./ankerctl.py config import ~/.wine/drive_c/users/username/AppData/Roaming/eufyMake Studio Profile/cache/offline/user_info
   ```
   MacOS
   ```sh
   ./ankerctl.py config import $HOME/Library/Application\ Support/AnkerMake/AnkerMake_64bit_fp/login.json
   ```
   Windows
   ```sh
   python3 ankerctl.py config import %APPDATA%\Roaming\eufyMake Studio Profile\cache\offline\user_info
   ```

   Type `ankerctl.py config import -h` for more details on the import options. To learn more about the method used to extract the login information and add printers, see the [MQTT Overview](documentation/developer-docs/mqtt-overview.md) and [Example Files](documentation/developer-docs/example-file-usage) documentation.

   Alternatively, you can log in directly with email/password:

   ```sh
   ./ankerctl.py config login DE
   ```

   You will be prompted for email and password. If AnkerMake requires a CAPTCHA (usually after multiple failed attempts),
   the CLI will open it in your browser and ask for the answer.

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
> As an alternative to using "config import" on the command line, it is possible to upload `login.json` through the web interface.
> You can also use email/password login in the web UI (Setup tab). Either method will work fine.

## Usage

### Web Interface

1. Start the webserver by running one of the following commands in the folder you placed ankerctl in. You’ll need to have this running whenever you want to use the web interface or send jobs to the printer via a slicer:

   Docker Installation Method:

   ```sh
   # Build the image (match UID/GID to your host user)
   docker build -t django01982/ankerctl:local --build-arg UID=$(id -u) --build-arg GID=$(id -g) .

   # Copy .env.example to .env and adjust values, then start
   cp .env.example .env
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

### Authentication (API Key)

ankerctl supports optional API key authentication. When enabled, all web and API endpoints require a valid key.

**Enable via CLI:**

```sh
# Generate a random API key
./ankerctl.py config set-password

# Or set a specific key
./ankerctl.py config set-password my-secret-key

# Remove key (disable authentication)
./ankerctl.py config remove-password
```

**Enable via Docker (environment variable):**

```yaml
# In .env (see .env.example)
ANKERCTL_API_KEY=my-secret-key
```

**Using the key:**

- **Slicer (PrusaSlicer, OrcaSlicer, etc.):** Enter the key as the API Key in the printer settings (sent as `X-Api-Key` header)
- **Browser:** Append `?apikey=your-key` to the URL once — a session cookie is set automatically
- **No key set** = no authentication (backwards compatible, default behavior)
- The **WebUI is always readable** (status, video, etc.) — the key is only required for write operations (uploading files, sending gcode, controlling the printer)

### Environment Variables

ankerctl is configured via environment variables. For Docker deployments, copy `.env.example` to `.env` and adjust the values — Docker Compose loads them automatically.

| Variable | Default | Description |
|----------|---------|-------------|
| **Server** | | |
| `FLASK_HOST` | `127.0.0.1` | IP address the web server binds to |
| `FLASK_PORT` | `4470` | Port the web server listens on |
| **Upload** | | |
| `UPLOAD_MAX_MB` | `2048` | Maximum upload file size in MB |
| `UPLOAD_RATE_MBPS` | `2` | Upload speed to printer in Mbit/s (2, 4, 6, or 8) |
| **Security** | | |
| `ANKERCTL_API_KEY` | *(unset)* | API key for write-operation authentication |
| **Feature Flags** | | |
| `ANKERCTL_PRINT_CONTROLS` | *(unset)* | Show Pause/Resume/Stop buttons (experimental) |
| **Apprise Notifications** | | |
| `APPRISE_ENABLED` | `false` | Enable Apprise notifications |
| `APPRISE_SERVER_URL` | *(unset)* | Apprise API server URL |
| `APPRISE_KEY` | *(unset)* | Apprise notification key/ID |
| `APPRISE_TAG` | *(unset)* | Apprise tag filter |
| `APPRISE_EVENT_PRINT_STARTED` | `true` | Notify on print start |
| `APPRISE_EVENT_PRINT_FINISHED` | `true` | Notify on print finish |
| `APPRISE_EVENT_PRINT_FAILED` | `true` | Notify on print failure |
| `APPRISE_EVENT_GCODE_UPLOADED` | `true` | Notify on G-code upload |
| `APPRISE_EVENT_PRINT_PROGRESS` | `true` | Notify on progress updates |
| `APPRISE_PROGRESS_INTERVAL` | `25` | Progress notification interval (%) |
| `APPRISE_PROGRESS_INCLUDE_IMAGE` | `false` | Attach camera snapshot to progress |
| `APPRISE_PROGRESS_MAX` | `0` | Override progress scale (0 = auto) |
| `APPRISE_SNAPSHOT_QUALITY` | `hd` | Snapshot quality: `sd` or `hd` |
| `APPRISE_SNAPSHOT_FALLBACK` | `true` | Use G-code preview if live fails |
| `APPRISE_SNAPSHOT_LIGHT` | `false` | Turn on printer light for snapshot |
| **Print History** | | |
| `PRINT_HISTORY_RETENTION_DAYS` | `90` | Number of days to keep history entries |
| `PRINT_HISTORY_MAX_ENTRIES` | `500` | Maximum number of history entries to keep |
| **Timelapse** | | |
| `TIMELAPSE_ENABLED` | `false` | Enable automatic timelapse capture (requires ffmpeg) |
| `TIMELAPSE_INTERVAL_SEC` | `30` | Seconds between snapshot captures |
| `TIMELAPSE_MAX_VIDEOS` | `10` | Maximum number of timelapse videos to keep |
| `TIMELAPSE_SAVE_PERSISTENT` | `true` | Save assembled videos persistently |
| `TIMELAPSE_CAPTURES_DIR` | `/captures` | Directory for timelapse video storage |

> **Tip:** See [`.env.example`](.env.example) for a ready-to-use template with all variables and comments.

### Notifications (Apprise)

ankerctl supports push notifications via [Apprise](https://github.com/caronc/apprise), a universal notification library that supports 90+ notification services (Discord, Telegram, Slack, Pushover, email, and many more).

**Setup Options:**
1. **Web UI** (recommended): Configure in the Setup tab under Notifications
2. **Environment Variables**: Useful for Docker deployments (see below)

ankerctl requires an external Apprise API server (not the CLI tool). You can:
- Run the [Apprise API Docker container](https://github.com/caronc/apprise-api)
- Use a hosted Apprise API instance

**Configuration via Environment Variables:**

```sh
# Connection settings
APPRISE_ENABLED=true
APPRISE_SERVER_URL=http://apprise:8000  # Your Apprise API server URL
APPRISE_KEY=ankerctl                     # Apprise notification key/ID
APPRISE_TAG=critical                     # Optional: Apprise tag filter

# Event toggles (set to true/false)
APPRISE_EVENT_PRINT_STARTED=true         # Notify when print starts
APPRISE_EVENT_PRINT_FINISHED=true        # Notify when print completes
APPRISE_EVENT_PRINT_FAILED=true          # Notify when print fails
APPRISE_EVENT_GCODE_UPLOADED=true        # Notify when G-code uploaded
APPRISE_EVENT_PRINT_PROGRESS=true        # Notify on print progress updates

# Progress notification settings
APPRISE_PROGRESS_INTERVAL=25             # Progress interval (e.g., every 25%)
APPRISE_PROGRESS_INCLUDE_IMAGE=false     # Attach camera snapshot to progress notifications
APPRISE_SNAPSHOT_QUALITY=hd              # Snapshot quality: 'sd' or 'hd'
APPRISE_SNAPSHOT_FALLBACK=true           # Use G-code preview if live snapshot fails
APPRISE_PROGRESS_MAX=0                   # Override progress scale (0=auto)
```

**Testing Your Setup:**

1. Open Setup → Notifications in the web UI
2. Enter your Apprise server URL and key
3. Enable notifications and select desired events
4. Click **Send test** and verify the notification arrives
5. Test with real events:
   - Upload a G-code file → verify upload notification
   - Start a print → verify start/progress/finish notifications

**Image Attachments:**

When "Include image" is enabled for progress/finish notifications, ankerctl will:
1. Attempt to capture a live camera snapshot (requires `ffmpeg` installed)
2. If live capture fails and "Fallback to preview image" is enabled, attach the G-code preview image instead
3. If both fail, send text-only notification

**Note:** Live snapshots require an active PPPP connection and working video stream.

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

# set an API key for web authentication
./ankerctl.py config set-password

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

The goal of this project is to make the AnkerMake M5 usable and accessible using only Free and Open Source Software (FOSS).

This project is [licensed under the GNU GPLv3](LICENSE), and copyright © 2023 Christian Iversen.

Some icons from [IconFinder](https://www.iconfinder.com/iconsets/3d-printing-line), and licensed under [Creative Commons](https://creativecommons.org/licenses/by/3.0/)
