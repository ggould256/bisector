#!/bin/bash

set -ex

python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt

pushd src
python3 -m unittest core.test.history_probability_test
python3 -m unittest core.test.search_test
popd

deactivate
