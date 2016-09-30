#source this file.


_BUCKET="testbucket"
checkmounted(){ grep -qs "$1" "/proc/mounts";}


if checkmounted "$_BUCKET"; then
	echo "S3 bucket is mounted."
else 
	echo "Mounting the bucket..."
	cmd = "goofys --endpoint s3.eu-central-1.amazonaws.com --sse testbcbio /mnt/$_BUCKET"
    echo cmd
    cmd
	if checkmounted "$_BUCKET"; then
		echo "Successfully mounted S3 bucket."
	else
		echo "Something went wrong with the mount."
		echo "That's all I know:"
		sudo grep "fuse\|goofys" /var/log/syslog | tail
	fi
fi

echo "BCBIO workdir is now $BCBIO_WORKDIR"
export BCBIO_WORKDIR=/mnt/testbucket/testworkdir

deactivate () {
	unset BCBIO_WORKDIR
}
