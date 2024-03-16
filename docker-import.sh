#!/bin/sh

set -e

if [ $# -eq 0 ]; then
    CONTAINER="ankerctl"
elif [ $# -eq 1 ]; then
    CONTAINER="$1"
else
    echo "usage: $0 [container-name]"
    echo ""
    echo "  Attempt to auto-import AnkerMake Slicer credentials"
    echo "  ('login.json') into the specified docker container."
    echo ""
    echo "  Container name default to 'ankerctl' if unspecified."
    exit 1
fi

if [ "$(docker container inspect -f "{{.State.Status}}" "${CONTAINER}")" != "running" ]; then
    echo ""
    echo ">> Container ${CONTAINER} is not running. Please start container before running this script! <<"
    exit 1
fi


if [ -f "./login.json" ]; then
    echo "** Importing ./login.json **"
    docker cp -L ./login.json ${CONTAINER}:/tmp
    if docker exec -it ${CONTAINER} /app/ankerctl.py -k config import /tmp/login.json; then
        echo "Configuration imported successfully. Restarting container..."
        docker restart ${CONTAINER}
        exit $?
    else
        echo "Configuration import failed :("
    fi
else
    WINEPREFIX=${WINEPREFIX:-$HOME/.wine}

    for root in "${APPDATA}" "${HOME}"; do
        for prefix in "Library/Application Support" "$WINEPREFIX/drive_c/users/${USER}/AppData/Local"; do
            for suffix in "AnkerMake/AnkerMake_64bit_fp/login.json" "Ankermake/AnkerMake_64bit_fp/login.json"; do
                name="$root/$prefix/$suffix";
                if [ -f "${name}" ]; then
                    echo "** Importing ${name} credentials **";
                    docker cp -L "${name}" ${CONTAINER}:/tmp
                    if docker exec -it ${CONTAINER} /app/ankerctl.py -k config import /tmp/login.json; then
                        echo "Configuration imported successfully. Restarting container..."
                        docker restart ${CONTAINER}
                        exit $?
                    else
                        echo "Configuration import failed :("
                    fi
                else
                    echo "** No ${name} credentials detected **";
                fi
            done
        done
    done
fi
