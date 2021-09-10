#!/bin/bash

BUILD_NAME="aws-fast-fixes"
CREDENTIALS_PATH="$HOME/.aws/credentials"
DOCKER_ARGS="-v ${CREDENTIALS_PATH}:/root/.aws/credentials:ro"

DOCKER_ARGS="${DOCKER_ARGS}"
docker build -t ${BUILD_NAME} .
IMAGE=${BUILD_NAME}

docker run -it --rm ${DOCKER_ARGS} ${IMAGE} "$@"
