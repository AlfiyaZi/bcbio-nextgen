#!/usr/bin/env bash

BCBIO_DIR=$(dirname "$(readlinkf `which bcbio_nextgen.py`)")
TEST_CLASS="test_automated_analysis.py:AutomatedAnalysisTest"

set -e

echo 
cmd="$BCBIO_DIR/nosetests -v -s $TEST_CLASS.$1"
echo $cmd
$cmd
