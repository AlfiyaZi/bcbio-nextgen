#!/usr/bin/env bash

BUCKET="testbucket"
checkmounted(){ grep -qs "$1" "/proc/mounts";}
ATTR=${1:-speed=1}
set -e

if [ -n "$1" ]; then
	# Remaining args are passed unmodified to the test runner.
	shift
fi

if checkmounted "$BUCKET"; then
	echo "S3 bucket is mounted."
else 
	echo "Mounting the bucket..."
	echo "$GOPATH/bin/goofys" --endpoint "s3.eu-central-1.amazonaws.com" --sse testbcbio "/mnt/$BUCKET"
	"$GOPATH/bin/goofys" --endpoint "s3.eu-central-1.amazonaws.com" --sse testbcbio "/mnt/$BUCKET"
	if checkmounted "$BUCKET"; then
		echo "Successfully mounted S3 bucket."
	else
		echo "Something went wrong with the mount."
		echo "That's all I know:"
		sudo grep "fuse\|goofys" /var/log/syslog | tail
	fi
fi
