echo "Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get -y update
sudo apt-get install -y git python-pip python-dev apt-get install software-properties-common python-software-properties build-essential python-pyrex zlib1g-dev 
sudo add-apt-repository -y ppa:webupd8team/java 
sudo apt-get -y update
sudo apt-get install -y oracle-java8-installer

echo "Installing pyhton pachakges..."
pip install -U pip
pip install Cython
pip install toolz
pip install umis

chmod -R 777 /usr/local  # to avoid problems with bcbio installation
exit
echo
echo "Installing bcbio..."
python /vagrant/scripts/bcbio_nextgen_install.py /usr/local/share/bcbio --tooldir=/usr/local --nodata

bcbio_nextgen.py upgrade --tools --toolplus gatk=/vagrant/GenomeAnalysisTK.jar --tooldir=/usr/local

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
