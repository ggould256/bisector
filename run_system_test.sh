#!/bin/bash

REPO_DIR=$(realpath "$(dirname "$0")")
export PYTHONPATH=$PYTHONPATH:`pwd`
temp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'bisector_system_test')
set -ex

test_fixture_dir="$temp_dir/fixture"
rm -rf $test_fixture_dir
revisions=`python3 git_fuzzy_bisector/fixture/fixture.py --initial-prob 0.6 --final-prob 0.4 --quiet $test_fixture_dir`
cd $test_fixture_dir
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e $REPO_DIR
git fuzzy-bisect --test_limit 20 $revisions ./run.py

rm -rf $temp_dir
