# Installation (Docker)

## login.json pre-requisites for Linux Install

### AnkerMake Slicer installed on another Machine

1. Install the [AnkerMake slicer](https://www.ankermake.com/software) on a supported Operating System.  Make sure you open it and login via the “Account” dropdown in the top toolbar.

2. Retreive the ```login.json``` file (Windows: ```user_info```) from the supported operating system:

  Windows Default Location:
  ```sh
  %APPDATA%\Roaming\eufyMake Studio Profile\cache\offline\user_info
  ```
   
  MacOS Default Location:
  ```sh
  $HOME/Library/Application\ Support/AnkerMake/AnkerMake_64bit_fp/login.json
   ```

3. Take said ```login.json``` file and store it in a location your docker instance will be able to access it from.

4. Now follow the Docker Compose Instructions below.

### Native Linux

1. Install the [AnkerMake slicer](https://www.ankermake.com/software) on Linux via emulation such as Wine.  Make sure you open it and login via the “Account” dropdown in the top toolbar.
   
2. Retreive the ```login.json``` file (Windows: ```user_info```) ```~/.wine/drive_c/users/$USER/AppData/Roaming/eufyMake Studio Profile/cache/offline/user_info```

3. Take said ```login.json``` file and store it in a location your docker instance will be able to access it from.

4. Now follow the Docker Compose Instructions below.

## Docker Compose Instructions

To start `ankerctl` using docker compose, run:

```sh
docker compose pull
docker compose up
```

### Customizing UID/GID

The Docker container runs as a non-root user `ankerctl` (UID/GID 1000 by default).
If your host user has different IDs, customize them in `docker-compose.yaml`:

```yaml
build:
    context: .
    args:
        UID: 1001   # your host UID (run: id -u)
        GID: 1001   # your host GID (run: id -g)
```

Or build directly:

```sh
docker compose build --build-arg UID=$(id -u) --build-arg GID=$(id -g)
```
