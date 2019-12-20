#!/usr/bin/env bash

__lang_setting() {
    case "$1" in
        CentOS)
            localedef -c -i en_US -f UTF-8 en_US.utf8
            export LANG=en_US.UTF-8
            ;;
        Ubuntu)
            locale-gen en_US.UTF-8
            update-locale LANG=en_US.UTF-8
            ;;
        *) echo "unknown target os for lang_setting: $1" ;;
    esac
}

XVFB=/usr/bin/Xvfb
XVFB_DISP=:99.0
XVFB_ARGS="$XVFB_DISP -screen 0 1024x768x24 -ac +extension GLX +render -noreset"
QT_PLATFORM='offscreen'

__start_Xvfb() {
    case "$1" in
        CentOS)
            export DISPLAY=$XVFB_DISP
            export QT_QPA_PLATFORM=$QT_PLATFORM
            $XVFB $XVFB_ARGS &
            ;;
        Ubuntu|Debian)
            export DISPLAY=$XVFB_DISP
            export QT_QPA_PLATFORM=$QT_PLATFORM
            start-stop-daemon --start -b -x $XVFB -- $XVFB_ARGS
            ;;
        *) echo "unknown target os for xvfb: $1" ;;
    esac
}


echo "Start to prepare environment for job: {$1}"

JOB_SCOPE=$(echo $1 | cut -f1 -d' ')
JOB_TYPE=$(echo $1 | cut -f2 -d' ')
TARGET_OS=$(echo $1 | cut -f3 -d' ')

REL_OS_NAME=$(lsb_release -is)

__lang_setting $REL_OS_NAME
git clean -fdx

__start_Xvfb $REL_OS_NAME

