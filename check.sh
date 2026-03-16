#!/bin/bash

set -e
rm -rf .test_venv
python3.12 -m venv .test_venv
.test_venv/bin/pip3 install -U pip
.test_venv/bin/pip3 install -e .
.test_venv/bin/ruff check .
.test_venv/bin/py.test
