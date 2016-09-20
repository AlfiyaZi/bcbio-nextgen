echo "Installing system packages..."
sudo apt-get update 1>/dev/null
sudo apt-get install -y \
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
	sudo add-apt-repository -y ppa:nilarimogard/webupd8
	sudo apt-get update 1>/dev/null
	sudo apt-get install -y launchpad-getkeys
	sudo launchpad-getkeys
	echo
	echo "Adding ppa:webupd8team/java repo..."
	sudo add-apt-repository -y ppa:webupd8team/java
	sudo apt-get update 1>/dev/null
	wget --no-check-certificate https://github.com/aglover/ubuntu-equip/raw/master/equip_java8.sh && bash equip_java8.sh
	sudo apt-get install -y oracle-java8-installer --force-yes 
fi;

echo "Installing pyhton pachakges..."
pip install -U pip
pip install Cython
pip install toolz
pip install umis


echo
echo "Installing bcbio..."
chmod -R 777 /usr/local  # to avoid problems with bcbio installation
cd /vagrant

su vagrant -c "python scripts/bcbio_nextgen_install.py /usr/local/share/bcbio --tooldir=/usr/local --nodata"

su vagrant -c "bcbio_nextgen.py upgrade --tools --toolplus gatk=/vagrant/GenomeAnalysisTK.jar --tooldir=/usr/local 1>/dev/null"

echo
echo "Installing go lang..."
curl -O https://storage.googleapis.com/golang/go1.6.linux-amd64.tar.gz
tar -xvf go1.6.linux-amd64.tar.gz
mv go /usr/local
export GOPATH=$HOME/gowork

echo "Installing kahing/goofys..."
go get github.com/kahing/goofys
go install github.com/kahing/goofys

echo "Preapring a mount directory"
mkdir /mnt/testbucket
chmod 777 /mnt/testbucket

echo
echo "Please add your AWS credentials to ~/.aws/credentials before working with S3 bucket."
