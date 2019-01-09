#!/bin/bash

pipenv install
pipenv check

pushd src
pipenv run python3 -m unittest core.test.history_probability_test
popd
