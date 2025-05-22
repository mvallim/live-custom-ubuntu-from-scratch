#!/bin/bash

set -e                  # exit on error
set -o pipefail         # exit on pipeline error
set -u                  # treat unset variable as error

# Handle errors so the host doesn't lock up
trap 'chroot_unbind $? $LINENO' ERR

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

CMD=(setup_host install_pkg build_image finish_up)

function help() {
	# if $1 is set, use $1 as headline message in help()
	if [ -z ${1+x} ]; then
		echo -e "This script builds Ubuntu from scratch"
		echo -e
	else
		echo -e $1
		echo
	fi
	echo -e "Supported commands : ${CMD[*]}"
	echo -e
	echo -e "Syntax: $0 [start_cmd] [-] [end_cmd]"
	echo -e "\trun from start_cmd to end_end"
	echo -e "\tif start_cmd is omitted, start from first command"
	echo -e "\tif end_cmd is omitted, end with last command"
	echo -e "\tenter single cmd to run the specific command"
	echo -e "\tenter '-' as only argument to run all commands"
	echo -e
	exit 0
}

function find_index() {
	local ret;
	local i;
	for ((i=0; i<${#CMD[*]}; i++)); do
		if [ "${CMD[i]}" == "$1" ]; then
			index=$i;
			return;
		fi
	done
	help "Command not found : $1"
}

function check_host() {
	if [ $(id -u) -ne 0 ]; then
		echo "This script should be run as 'root'"
		exit 1
	fi

	export HOME=/root
	export LC_ALL=C
}

function setup_host() {
	echo "=====> running setup_host ..."

   cat <<EOF > /etc/apt/sources.list
deb $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION main restricted universe multiverse
deb-src $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION main restricted universe multiverse

deb $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION-security main restricted universe multiverse
deb-src $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION-security main restricted universe multiverse

deb $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION-updates main restricted universe multiverse
deb-src $TARGET_UBUNTU_MIRROR $TARGET_UBUNTU_VERSION-updates main restricted universe multiverse
EOF

	cat <<EOF > /etc/casper.conf
# This file should go in /etc/casper.conf
# Supported variables are:
# USERNAME, USERFULLNAME, HOST, BUILD_SYSTEM, FLAVOUR

export USERNAME="live"
export USERFULLNAME="Live session user"
export HOST="privOS"
export BUILD_SYSTEM="Ubuntu"

# USERNAME and HOSTNAME as specified above won't be honoured and will be set to
# flavour string acquired at boot time, unless you set FLAVOUR to any
# non-empty string.

export FLAVOUR="Ubuntu"
EOF

	echo "$TARGET_NAME" > /etc/hostname

	# we need to install systemd first, to configure machine id
	apt-get update
	apt-get install -y libterm-readline-gnu-perl systemd-sysv

	#configure machine id
	dbus-uuidgen > /etc/machine-id
	ln -fs /etc/machine-id /var/lib/dbus/machine-id

	# don't understand why, but multiple sources indicate this
	dpkg-divert --local --rename --add /sbin/initctl
	ln -s /bin/true /sbin/initctl
}

# Load configuration values from file
function load_config() {
	if [[ -f "$SCRIPT_DIR/config.sh" ]]; then
		. "$SCRIPT_DIR/config.sh"
	elif [[ -f "$SCRIPT_DIR/default_config.sh" ]]; then
		. "$SCRIPT_DIR/default_config.sh"
	else
		>&2 echo "Unable to find default config file  $SCRIPT_DIR/default_config.sh, aborting."
		exit 1
	fi
}

function chroot_unbind() {
	chroot umount /proc
	chroot umount /sys
	chroot umount /dev/pts
}

function install_pkg() {
	echo "=====> running install_pkg ... will take a long time ..."
	apt-get -y upgrade

	# install live packages
	apt-get install -y \
		sudo \
		ubuntu-standard \
		casper \
		discover \
		laptop-detect \
		os-prober \
		network-manager \
		net-tools \
		iw \
		locales \
		grub-common \
		grub-gfxpayload-lists \
		grub-pc \
		grub-pc-bin \
		grub2-common \
		grub-efi-amd64-signed \
		shim-signed \
		mtools \
		unzip \
		binutils \
		ubuntu-drivers-common

	case $TARGET_UBUNTU_VERSION in
		"focal" | "bionic")
			apt-get install -y lupin-casper
			;;
		*)
			echo "Package lupin-casper is not needed. Skipping."
			;;
	esac

	# install kernel
	apt-get install -y --no-install-recommends $TARGET_KERNEL_PACKAGE

	# graphic installer - ubiquity kde
	apt install -y ubiquity \
		ubiquity-casper \
		ubiquity-frontend-gtk \
		ubiquity-slideshow-kubuntu

	# Call into config function
	customize_image

	# remove unused and clean up apt cache
	apt-get autoremove -y

	# final touch
	dpkg-reconfigure locales

	# Set up network manager
	cat << EOF > /etc/NetworkManager/NetworkManager.conf
[main]
rc-manager=resolvconf
plugins=ifupdown,keyfile
dns=dnsmasq
[ifupdown]
managed=false
EOF
	dpkg-reconfigure network-manager
	cat << EOF > /etc/netplan/01-network-manager-all.yaml
network:
  version: 2
  renderer: NetworkManager
EOF
	apt-get clean -y
}

function build_image() {
	echo "=====> running build_image ..."

	rm -rf /image

	mkdir -p /image/{casper,isolinux,install}

	pushd /image

	# copy kernel files
	cp /boot/vmlinuz-**-**-generic casper/vmlinuz
	cp /boot/initrd.img-**-**-generic casper/initrd

	# memtest86
	wget --progress=dot https://memtest.org/download/v7.00/mt86plus_7.00.binaries.zip -O install/memtest86.zip
	unzip -p install/memtest86.zip memtest64.bin > install/memtest86+.bin
	unzip -p install/memtest86.zip memtest64.efi > install/memtest86+.efi
	rm -f install/memtest86.zip

	# grub
	touch ubuntu
	cat <<EOF > isolinux/grub.cfg

search --set=root --file /ubuntu

insmod all_video

set default="0"
set timeout=30

menuentry "Try PrivOS without installing" {
	linux /casper/vmlinuz boot=casper nopersistent toram quiet splash ---
	initrd /casper/initrd
}

menuentry "Install PrivOS" {
	linux /casper/vmlinuz boot=casper only-ubiquity quiet splash ---
	initrd /casper/initrd
}

menuentry "Check disc for defects" {
	linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
	initrd /casper/initrd
}

grub_platform
if [ "\$grub_platform" = "efi" ]; then
menuentry 'UEFI Firmware Settings' {
	fwsetup
}

menuentry "Test memory Memtest86+ (UEFI)" {
	linux /install/memtest86+.efi
}
else
menuentry "Test memory Memtest86+ (BIOS)" {
	linux16 /install/memtest86+.bin
}
fi
EOF

	# generate manifest
	dpkg-query -W --showformat='${Package} ${Version}\n' | sudo tee casper/filesystem.manifest

	cp -v casper/filesystem.manifest casper/filesystem.manifest-desktop

	for pkg in $TARGET_PACKAGE_REMOVE; do
		sudo sed -i "/^$pkg/d" casper/filesystem.manifest-desktop
	done

	# create diskdefines
	cat <<EOF > README.diskdefines
#define DISKNAME  ${GRUB_LIVEBOOT_LABEL}
#define TYPE  binary
#define TYPEbinary  1
#define ARCH  amd64
#define ARCHamd64  1
#define DISKNUM  1
#define DISKNUM1  1
#define TOTALNUM  0
#define TOTALNUM0  1
EOF

	# copy EFI loaders
	cp /usr/lib/shim/shimx64.efi.signed.previous isolinux/bootx64.efi
	cp /usr/lib/shim/mmx64.efi isolinux/mmx64.efi
	cp /usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed isolinux/grubx64.efi

	# create a FAT16 UEFI boot disk image containing the EFI bootloaders
	(
		cd isolinux && \
		dd if=/dev/zero of=efiboot.img bs=1M count=10 && \
		mkfs.vfat -F 16 efiboot.img && \
		LC_CTYPE=C mmd -i efiboot.img efi efi/ubuntu efi/boot && \
		LC_CTYPE=C mcopy -i efiboot.img ./bootx64.efi ::efi/boot/bootx64.efi && \
		LC_CTYPE=C mcopy -i efiboot.img ./mmx64.efi ::efi/boot/mmx64.efi && \
		LC_CTYPE=C mcopy -i efiboot.img ./grubx64.efi ::efi/boot/grubx64.efi && \
		LC_CTYPE=C mcopy -i efiboot.img ./grub.cfg ::efi/ubuntu/grub.cfg
	)

	# create a grub BIOS image
	grub-mkstandalone \
	  --format=i386-pc \
	  --output=isolinux/core.img \
	  --install-modules="linux16 linux normal iso9660 biosdisk memdisk search tar ls" \
	  --modules="linux16 linux normal iso9660 biosdisk search" \
	  --locales="" \
	  --fonts="" \
	  "boot/grub/grub.cfg=isolinux/grub.cfg"

	# combine a bootable Grub cdboot.img
	cat /usr/lib/grub/i386-pc/cdboot.img isolinux/core.img > isolinux/bios.img

	# generate md5sum.txt
	/bin/bash -c "(find . -type f -print0 | xargs -0 md5sum | grep -v -e 'isolinux' > md5sum.txt)"

	popd # return initial directory
}

function finish_up() {
	echo "=====> finish_up"

	# truncate machine id (why??)
	truncate -s 0 /etc/machine-id

	# remove diversion (why??)
	rm /sbin/initctl
	dpkg-divert --rename --remove /sbin/initctl

	rm -rf /tmp/* ~/.bash_history
}

# =============   main  ================

load_config
check_host

# check number of args
if [[ $# == 0 || $# > 3 ]]; then help; fi

# loop through args
dash_flag=false
start_index=0
end_index=${#CMD[*]}
for ii in "$@";
do
	if [[ $ii == "-" ]]; then
		dash_flag=true
		continue
	fi
	find_index $ii
	if [[ $dash_flag == false ]]; then
		start_index=$index
	else
		end_index=$(($index+1))
	fi
done
if [[ $dash_flag == false ]]; then
	end_index=$(($start_index + 1))
fi

# loop through the commands
for ((ii=$start_index; ii<$end_index; ii++)); do
	${CMD[ii]}
done

echo "$0 - Initial build is done!"
