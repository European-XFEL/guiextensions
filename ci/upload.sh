#!/usr/bin/env bash

# This script should be called after the build.sh script, so then karabo
# will already be installed and activated

JOB_SCOPE=$(echo $1 | cut -f1 -d' ')
JOB_TYPE=$(echo $1 | cut -f2 -d' ')
TARGET_OS=$(echo $1 | cut -f3 -d' ')

echo "Starting release job for $JOB_SCOPE"

if [[ "$JOB_SCOPE" != "release" ]]; then
    exit
fi

SSH_USER_HOST=xdata@exflserv05
CURL_PREFIX=http://exflserv05.desy.de/karabo

COMMIT_TAG=$CI_COMMIT_REF_NAME
DESTINATION_PATH=karaboExtensions/tags/$COMMIT_TAG

pushd $CI_PROJECT_DIR

echo "Creating wheel at $CI_PROJECT_DIR"

# Create wheel in dist/
python setup.py bdist_wheel

# Rename the wheel file
WHEEL_FILE=GUI_Extensions-$COMMIT_TAG-py3.whl
mv $CI_PROJECT_DIR/dist/GUI_Extensions-*.whl $WHEEL_FILE

# Make directories on remote
SSH_KARABO_DIR=/var/www/html/karabo

echo "Creating remote directories: $SSH_KARABO_DIR/$DESTINATION_PATH"
sshpass -p "$XDATA_PWD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SSH_USER_HOST "mkdir -p $SSH_KARABO_DIR/$DESTINATION_PATH"

# Copy wheel to correct directory
SSH_PREFIX=$SSH_USER_HOST:$SSH_KARABO_DIR

echo "Moving $WHEEL_FILE to $SSH_PREFIX/$DESTINATION_PATH"
sshpass -p "$XDATA_PWD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $WHEEL_FILE $SSH_PREFIX/$DESTINATION_PATH

popd
