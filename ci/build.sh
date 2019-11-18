#!/usr/bin/env bash

export REL_PROJECT_NAME=$CI_PROJECT_NAME
export REL_TAG=$CI_BUILD_REF_NAME
export FRAMEWORK_DIR=/root/Framework

git clone https://$XFEL_TOKEN@git.xfel.eu/gitlab/Karabo/Framework.git $FRAMEWORK_DIR
cd $FRAMEWORK_DIR
. ci/utils/enable_internet.sh


# Create a test environment for the created package
cd src/pythonGui/
conda remove -n karabogui --yes --all
conda devenv
source activate karabogui
python setup.py --version

# Install guiextensions
cd $CI_PROJECT_DIR
pip install --upgrade .
