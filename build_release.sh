#!/bin/bash

set -e

SERVICE_NAME="innatis"

BASE_STRING=$(cat VERSION)
BASE_LIST=($(echo "$BASE_STRING" | tr '.' ' '))
V_MAJOR=${BASE_LIST[0]}
V_MINOR=${BASE_LIST[1]}
V_PATCH=${BASE_LIST[2]}
echo -e "Current version: $BASE_STRING"
V_MINOR=$((V_MINOR + 1))
V_PATCH=0
SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH"
CREDS_LOCATION=$1


check_credential_file_exists ()
{
    if [ ! -z "${CREDS_LOCATION}" ]; then
        echo "credentials were passed in as argument"
        PYPIRC="creds"
    elif [ -f .pypirc ]; then
        echo "found .pypirc in project directory..."
        PYPIRC="here"
    elif [ -f ~/.pypirc ]; then
        echo "found .pypirc in user home directory..."
        PYPIRC="root"
    else
        echo "## MISSING .pypirc file, can't release to PyPi!"
        exit 1
    fi
}

update_deps ()
{
    python3 -m pip install -U setuptools wheel
    python3 -m pip install -r requirements.txt
}

run_tests ()
{
    echo "running test suite"
    python3 innatis/test.py
}

bump_version ()
{
    echo "$SUGGESTED_VERSION" > VERSION
}

create_dist ()
{
    python3 setup.py sdist
}

upload_to_pypi ()
{
    echo "uploading to pypi"
    if [ $PYPIRC = "here" ]; then
        twine upload --config-file .pypirc dist/"$SERVICE_NAME"-"$SUGGESTED_VERSION".tar.gz
    elif [ $PYPIRC = "creds" ]; then
        twine upload --config-file "$CREDS_LOCATION" dist/"$SERVICE_NAME"-"$SUGGESTED_VERSION".tar.gz
    else
        twine upload --config-file ~/.pypirc dist/"$SERVICE_NAME"-"$SUGGESTED_VERSION".tar.gz
    fi
}

# -------------#
# run the code #
# -------------#

check_credential_file_exists
update_deps
run_tests
bump_version
create_dist
upload_to_pypi
