#!/bin/bash

if [ -f '.env' ]; then
  export $(grep -v '^#' .env | xargs)
else
  FLASK_HOST=127.0.0.1
  FLASK_PORT=4470
  BUILD_IMAGE=""
  ANKERCTL_DATA=ankerctl_vol
fi


print_usage() {

  echo "Usage: $0 [option] <command>"
  echo ""
  echo "Options:"
  echo ""
  echo "    -o          Open mode. Allow connections from the network"
  echo "    -b          Build the docker image from source"
  echo "    -i          Interactive mode. Blocks to run ankerctl. You can see the logging output"
  echo "    -p <port>   Port for Ankerctl web interface"
  echo "    -d <data>   Ankerctl data volume"
  echo ""
  echo "Commands:"
  echo "    up          Run the docker container"
  echo "    down        Stop the docker container"
}


exit_error() {
  print_usage
  exit 1
}

if [ $# -eq 0 ]; then
  print_usage
  exit 0
fi

OPT_MATCHES=':obip:d:'

while getopts "${OPT_MATCHES}" options; do
  case "${options}" in
    o) FLASK_HOST=0.0.0.0 ;;
    b) BUILD_IMAGE="1" ;;
    p) FLASK_PORT=${OPTARG} ;;
    i) INTERACTIVE="1" ;;
    d) ANKERCTL_DATA=${OPTARG} ;;
    :)
      echo "Error: -${OPTARG} requires an argument"
      exit_error
      ;;
    *)
      exit_error
      ;;
  esac
done

COMMAND=${@:$OPTIND:1}
EXTRA=${@:$OPTIND+1:1}

if [ ! -z "${EXTRA}" ]; then
  echo "No parameters allowed after command"
  exit_error
fi

echo "Command: ${COMMAND}"

case "${COMMAND}" in
  up)
    if [ ! -z "${BUILD_IMAGE}" ]; then
      # build docker image
      COMPOSE_EXTRA_PARAMS="${COMPOSE_EXTRA_PARAMS} --build "
    fi
    if [ -z "${INTERACTIVE}" ]; then
      COMPOSE_EXTRA_PARAMS="${COMPOSE_EXTRA_PARAMS} -d "
    fi

    FLASK_HOST=${FLASK_HOST} FLASK_PORT=${FLASK_PORT} ANKERCTL_DATA=${ANKERCTL_DATA} docker-compose up ${COMPOSE_EXTRA_PARAMS}

    cat << EOF > ./.env
FLASK_HOST=${FLASK_HOST}
FLASK_PORT=${FLASK_PORT}
ANKERCTL_DATA=${ANKERCTL_DATA}
EOF

    ;;

  down)
    docker-compose down
    ;;

  *)
    echo "Unrecognized command: ${CMD}"
    echo ""
    exit_error
    ;;
esac
