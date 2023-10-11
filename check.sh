#!/bin/bash


python3 -m venv .venv
. .venv/bin/activate
pip install -U pip

set -e

pip3 install -r requirements.txt >/dev/null

set -x

pushd src
python3 -m unittest core.test.history_probability_test
python3 -m unittest core.test.search_test
popd

deactivate
