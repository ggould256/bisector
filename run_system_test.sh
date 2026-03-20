#!/bin/bash

REPO_DIR=$(realpath "$(dirname "$0")")
export PYTHONPATH=$PYTHONPATH:`pwd`
temp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'bisector_system_test')
set -ex

test_fixture_dir="$temp_dir/fixture"
rm -rf $test_fixture_dir
revisions=`python3 git_fuzzy_bisector/fixture/fixture.py --initial-prob 0.8 --final-prob 0.6 --quiet $test_fixture_dir`
cd $test_fixture_dir
python3 -m venv $temp_dir/venv
$temp_dir/venv/bin/pip install -U pip
$temp_dir/venv/bin/pip install -e $REPO_DIR

# Activate the venv to cause fuzzy-bisect to be a git subcommand.
. $temp_dir/venv/bin/activate
echo "Test fixture is ready, running fuzzy-bisect."
git fuzzy-bisect --test_limit 50 $revisions ./run.py
deactivate

rm -rf $temp_dir
