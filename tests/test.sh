#!/usr/bin/env bash

readlinkf(){ perl -MCwd -e 'print Cwd::abs_path shift' $1;}

BCBIO_DIR=$(dirname "$(readlinkf `which bcbio_nextgen.py`)")
TEST_CLASS="test_automated_analysys.py:AutomatedAnalysisTest"

set -e
unset PYTHONHOME
unset PYTHONPATH
export PYTHONNOUSERSITE=1
unset BCBIO_WORKDIR

for i in "$@" ; do
    if [[ $i == "-m" ]] ; then
        /bin/bash ./mount.sh
        export BCBIO_WORKDIR=/mnt/testbucket/testworkdir
        break
    fi
done


echo 
cmd="$BCBIO_DIR/nosetests -v -s $TEST_CLASS.$1"
echo $cmd
$cmd
