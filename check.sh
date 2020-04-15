#!/bin/bash

pipenv install

# pipenv check is, mysteriously, adware: https://github.com/pypa/pipenv/issues/4188
# pipenv check

pushd src
pipenv run python3 -m unittest core.test.history_probability_test
pipenv run python3 -m unittest core.test.search_test
popd
