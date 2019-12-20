#!/usr/bin/env bash

pushd $CI_PROJECT_DIR
nosetests .
popd
