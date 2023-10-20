#!/bin/bash

set -e
python3 -m venv .venv
. .venv/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt >/dev/null
pip3 install -e .

set -x
python3 -m unittest git_fuzzy_bisector.core.test.history_probability_test
python3 -m unittest git_fuzzy_bisector.core.test.search_test
set +x

deactivate
