#!/bin/bash

export PYTHONPATH=$PYTHONPATH:`pwd`/src
temp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'bisector_system_test')
set -ex

test_fixture_dir="$temp_dir/fixture"
rm -rf $test_fixture_dir
revisions=`python3 git_fuzzy_bisector/fixture/fixture.py --initial-prob 0.6 --final-prob 0.4 --quiet $test_fixture_dir`
cd $test_fixture_dir
git-fuzzy-bisect --test_limit 20 $revisions ./run.py

rm -rf $temp_dir
