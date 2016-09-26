set -e
export DEBIAN_FRONTEND=noninteractive

echo "Installing system packages..."
apt-get update 1>/dev/null
apt-get install -y \
	curl \
	vim \
	git \
	software-properties-common \
	python-pip \
	python-dev \
	python-software-properties \
	build-essential \
	python-pyrex \
	zlib1g-dev 
if ! type -p java; then
	echo
	echo "Installing Java..."
	echo "Adding ppa:nilarimogard/webupd8 repo..."
	add-apt-repository -y ppa:nilarimogard/webupd8
	apt-get update 1>/dev/null
	apt-get install -y launchpad-getkeys
	launchpad-getkeys
	echo
	echo "Adding ppa:webupd8team/java repo..."
	add-apt-repository -y ppa:webupd8team/java
	apt-get update 1>/dev/null
	wget --no-check-certificate https://github.com/aglover/ubuntu-equip/raw/master/equip_java8.sh
	/bin/bash equip_java8.sh
	apt-get install -y oracle-java8-installer --force-yes 
fi;

echo "Installing pyhton packages..."
pip install -U pip
pip install Cython 1>/dev/null
pip install toolz 1>/dev/null
pip install umis 1>/dev/null


echo "============================================="
echo "Installing bcbio..."
chmod -R 777 /usr/local  # to avoid problems with bcbio installation
cd /vagrant

su vagrant -c "python scripts/bcbio_nextgen_install.py /usr/local/share/bcbio --nodata --tooldir=/usr/local 1>/dev/null"

su vagrant -c "bcbio_nextgen.py upgrade --tools --toolplus gatk=/home/vagrant/GenomeAnalysisTK.jar --tooldir=/usr/local 1>/dev/null"

echo "============================================="
echo "Installing go lang..."
curl -s -O https://storage.googleapis.com/golang/go1.6.linux-amd64.tar.gz
tar -xf go1.6.linux-amd64.tar.gz
mv go /usr/local
export PATH=$PATH:/usr/local/go/bin
echo "export PATH=\$PATH:/usr/local/go/bin" >> /home/vagrant/.profile
export GOPATH=$HOME/gowork
echo "export GOPATH=\$HOME/work" >> /home/vagrant/.profile

echo "Installing kahing/goofys..."
go get github.com/kahing/goofys
go install github.com/kahing/goofys

echo "Preparing a mount directory"
mkdir /mnt/testbucket
chmod 777 /mnt/testbucket

echo
echo "Please add your AWS credentials to ~/.aws/credentials before working with S3 bucket."
