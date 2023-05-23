# Installation (Docker)

## Linux

1a. Install the [AnkerMake slicer](https://www.ankermake.com/software) on a supported Operating System. Make sure you open it and login via the “Account” dropdown in the top toolbar.

1b. Install the [AnkerMake slicer](https://www.ankermake.com/software) on Linux via emulation such as Wine.

2a. Retreive the ```login.json``` file from the supported operating system:

      Windows Default Location:
   
         ```%APPDATA%\AnkerMake\AnkerMake_64bit_fp\login.json```
   
      MacOS Default Location:
   
         ```$HOME/Library/Application\ Support/AnkerMake/AnkerMake_64bit_fp/login.json```
   
2b. Retreive the ```login.json``` file ```~/.wine/drive_c/users/$USER/AppData/Local/AnkerMake/AnkerMake_64bit_fp/login.json```

3. Take said ```login.json``` file and store it in a location your docker instance will be able to access it from.

4a. Run ```docker compose up``` if you want to have Docker Compose build most of your container

4b. Run the following commands:

```sh
docker build -t ankerctl .
```

Example usage (no peristent storage)
```bash
docker run \
  -v "<replace with location of your login.json file>:/tmp/login.json" \
  ankerctl config decode /tmp/login.json
```

Example usage (with peristent storage)
```bash
# create volume where we can store configs
docker volume create ankerctl_vol

# generate /root/.config/ankerctl/default.json which is mounted to the docker volume
docker run \
  -v ankerctl_vol:/root/.config/ankerctl \
  -v "<replace with location of your login.json file>:/tmp/login.json" \
  ankerctl config import /tmp/login.json

# Now that there is a /root/.config/ankerctl/default.json file that persists in the docker volume
# we can run ankerctl without having to specify the login.json file
docker run \
  -v ankerctl_vol:/root/.config/ankerctl \
  ankerctl config show
```
Example usage of webserver
```sh
docker run \
  -v ankerctl_vol:/root/.config/ankerctl \
  -v "<replace with location of your login.json file>:/tmp/login.json" \
  ankerctl webserver run
