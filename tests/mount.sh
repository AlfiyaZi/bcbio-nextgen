#source this file.


_BUCKET="testbucket"
checkmounted(){ grep -s "$1" "/proc/mounts";}


if checkmounted "$_BUCKET"; then
	echo "S3 bucket is mounted."
else 
	echo "Mounting the bucket..."
	cmd="goofys --endpoint s3.eu-central-1.amazonaws.com --sse testbcbio /mnt/$_BUCKET"
	echo $cmd
	$cmd
	if checkmounted "$_BUCKET"; then
		echo "Successfully mounted S3 bucket."
	else
		echo "Something went wrong with the mount."
		echo "That's all I know:"
		sudo grep "fuse\|goofys" /var/log/syslog | tail
	fi
fi

export BCBIO_WORKDIR=/mnt/testbucket/testworkdir
echo "BCBIO workdir is now $BCBIO_WORKDIR"

deactivate () {
	unset BCBIO_WORKDIR
	echo "Bcbio workdir is no longer $BCBIO_WORKDIR"
}
