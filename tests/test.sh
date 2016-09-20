#!/usr/bin/env bash

readlinkf(){ perl -MCwd -e 'print Cwd::abs_path shift' $1;}

BCBIO_DIR=$(dirname "$(readlinkf `which bcbio_nextgen.py`)")
# 
# unset PYTHONHOME
# unset PYTHONPATH
# export PYTHONNOUSERSITE=1
# 
echo "$BCBIO_DIR/nosetests" -v -s test_automated_analysys.py:AutomatedAnalysisTest."$1"
echo
"$BCBIO_DIR/nosetests" -v -s test_automated_analysys.py:AutomatedAnalysisTest."$1"
