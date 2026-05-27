#!/bin/bash

apt-get install -y \
        sudo \
        binutils \
        casper \
        discover \
        inetutils-ping \
		iw \
        laptop-detect \
        mtools \
        os-prober \
        netplan.io \
        network-manager \
        net-tools \
        ubuntu-standard \
		unzip

case ${TARGET_UBUNTU_VERSION} in
	"focal" | "bionic")
		apt-get install -y lupin-casper
            ;;
       	*)
     	printf "Package lupin-casper is not needed. Skipping.\n"
            ;;
esac
