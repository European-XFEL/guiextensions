#!/usr/bin/env bash

pushd $CI_PROJECT_DIR
nosetests . --ignore-files="test_ipm_quadrant.py"
popd