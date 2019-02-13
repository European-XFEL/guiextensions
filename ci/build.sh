#!/usr/bin/env bash

export REL_OS_NAME=$(lsb_release -is)
export REL_OS_VERS_LONG=$(lsb_release -rs | sed -r "s/^([0-9]+).*/\1/")
export REL_PROJECT_NAME=$CI_PROJECT_NAME
export REL_TAG=$CI_BUILD_REF_NAME
export KARABO_TAG="Nightly"
export KARABO_BROKER_TOPIC="gitlab_ci_$CI_JOB_ID"

# Install karabo
curl http://exflserv05.desy.de/karabo/karaboFramework/nightly/karabo-$KARABO_TAG-Release-$REL_OS_NAME-$REL_OS_VERS_LONG-x86_64.sh > karabo.sh
bash karabo.sh --prefix=/root
source /root/karabo/activate

# Install guiextensions
pushd $CI_PROJECT_DIR

echo "Installing $REL_PROJECT_NAME/$REL_TAG"
karabo -g https://$XFEL_TOKEN@git.xfel.eu/gitlab install $REL_PROJECT_NAME $REL_TAG
pip install --upgrade .

popd