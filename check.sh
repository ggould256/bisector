#!/bin/bash

set -e
python3 -m venv .venv
. .venv/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt >/dev/null

pushd src
set -x

python3 -m unittest core.test.history_probability_test
python3 -m unittest core.test.search_test

set +x
popd

deactivate
