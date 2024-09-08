#!/bin/bash

set -e                  # exit on error
set -o pipefail         # exit on pipeline error
set -u                  # treat unset variable as error

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
        wireless-tools \
        wpagui \
        locales \
        grub-common \
        grub-gfxpayload-lists \
        grub-pc \
        grub-pc-bin \
        grub2-common \
        grub-efi-amd64-signed \
        shim-signed \
        mtools \
        binutils
    
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

    # graphic installer - ubiquity
    apt-get install -y \
        ubiquity \
        ubiquity-casper \
        ubiquity-frontend-gtk \
        ubiquity-slideshow-ubuntu \
        ubiquity-ubuntu-artwork

    # Call into config function
    customize_image

    # remove unused and clean up apt cache
    apt-get autoremove -y

    # final touch
    dpkg-reconfigure locales

    # network manager
    cat <<EOF > /etc/NetworkManager/NetworkManager.conf
[main]
rc-manager=none
plugins=ifupdown,keyfile
dns=systemd-resolved

[ifupdown]
managed=false
EOF

    dpkg-reconfigure network-manager

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
    cp /boot/memtest86+.bin install/memtest86+

    # memtest86++
    wget --progress=dot https://www.memtest86.com/downloads/memtest86-usb.zip -O install/memtest86-usb.zip
    unzip -p install/memtest86-usb.zip memtest86-usb.img > install/memtest86
    rm -f install/memtest86-usb.zip

    # grub
    touch ubuntu
    cat <<EOF > isolinux/grub.cfg

search --set=root --file /ubuntu

insmod all_video

set default="0"
set timeout=30

menuentry "Try Ubuntu FS without installing" {
    linux /casper/vmlinuz boot=casper nopersistent toram quiet splash ---
    initrd /casper/initrd
}

menuentry "Install Ubuntu FS" {
    linux /casper/vmlinuz boot=casper only-ubiquity quiet splash ---
    initrd /casper/initrd
}

menuentry "Check disc for defects" {
    linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
    initrd /casper/initrd
}

menuentry "Test memory Memtest86+ (BIOS)" {
    linux16 /install/memtest86+
}

menuentry "Test memory Memtest86 (UEFI, long load time)" {
    insmod part_gpt
    insmod search_fs_uuid
    insmod chain
    loopback loop /install/memtest86
    chainloader (loop,gpt1)/efi/boot/BOOTX64.efi
}
EOF

    # generate manifest
    dpkg-query -W --showformat='${Package} ${Version}\n' | sudo tee casper/filesystem.manifest

    cp -v casper/filesystem.manifest casper/filesystem.manifest-desktop

    for pkg in $TARGET_PACKAGE_REMOVE; do
        sudo sed -i "/$pkg/d" casper/filesystem.manifest-desktop
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

    # create certificates
    rm -rf /certificates 
    mkdir /certificates

    pushd /certificates

    # create the certificate template
    cat <<EOF > config.conf
[ req ]
default_bits            = 2048
default_md              = sha256
distinguished_name      = dn
prompt                  = no

[ dn ]
C                       = BR
ST                      = SP
L                       = Campinas
O                       = Scratch, Labs
OU                      = Labs
CN                      = \${ENV::CN}

[ root ]
basicConstraints        = critical,CA:TRUE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always,issuer
keyUsage                = critical,digitalSignature,keyEncipherment,keyCertSign,cRLSign

[ ca ]
basicConstraints        = critical,CA:TRUE,pathlen:0
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always,issuer:always
keyUsage                = critical,digitalSignature,keyEncipherment,keyCertSign,cRLSign

[ db ]
subjectKeyIdentifier    = hash
basicConstraints        = critical,CA:FALSE
keyUsage                = critical,keyEncipherment,dataEncipherment
authorityKeyIdentifier  = keyid,issuer:always
EOF

    # create the Root CA certificate
    CN="Root, CA" \
        openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout root.key \
            -days 3650 \
            -config config.conf \
            -extensions root \
            -out root.pem

    # create the intermediate CA certificate
    CN="Ubuntu live from scratch, CA" \
        openssl req -newkey rsa:2048 -nodes \
            -keyout ca.key \
            -config config.conf \
            -out ca.pem

    # create Database (DB) request certificate
    CN="Ubuntu live from scratch, Database" \
        openssl req -newkey rsa:2048 -nodes \
            -keyout db.key \
            -config config.conf \
            -out db.pem

    # sign the intermediate CA certificate with the Root CA certificate
    CN="Ubuntu live from scratch, CA" \
        openssl x509 -req \
            -extfile config.conf \
            -extensions ca \
            -in ca.pem \
            -CA root.pem \
            -CAkey root.key \
            -CAcreateserial \
            -out ca.pem \
            -days 3650 -sha256

    # sign Database (DB) certificate using your own CA
    CN="Ubuntu live from scratch, Database" \
        openssl x509 -req \
            -extfile config.conf \
            -extensions db \
            -in db.pem \
            -CA ca.pem \
            -CAkey ca.key \
            -CAcreateserial \
            -out db.pem \
            -days 3650 -sha256

    # create the intermediate CA certificate chain
    cat ca.pem root.pem > ca-chain.pem

    # verify the signatures
    openssl verify -CAfile ca-chain.pem db.pem

    # create DER version of our public key (CA)
    openssl x509 -outform DER -in ca.pem -out ca.cer

    popd # return to image directory

    # grub version/release
    GRUB_VERSION=`grub-mkstandalone -V | tr -s ' ' | cut -d' ' -f3 | cut -d'-' -f1`
    GRUB_RELEASE=`grub-mkstandalone -V | tr -s ' ' | cut -d' ' -f3`
    
    # create SBAT file
    cat <<EOF > isolinux/sbat.csv
sbat,1,SBAT Version,sbat,1,https://github.com/rhboot/shim/blob/main/SBAT.md
grub,1,Free Software Foundation,grub,$GRUB_VERSION,https://www.gnu.org/software/grub/
grub.ubuntu,1,Ubuntu,grub2,$GRUB_RELEASE,https://www.ubuntu.com/
EOF

    # create a grub UEFI image
    grub-mkstandalone \
      --format=x86_64-efi \
      --output=isolinux/grubx64.efi \
      --locales="" \
      --fonts="" \
      "boot/grub/grub.cfg=isolinux/grub.cfg"

    # fix secure boot grub
    sed -i 's/SecureBoot/SecureB00t/' isolinux/grubx64.efi

    # add .sbat sections
    objcopy --add-section .sbat=isolinux/sbat.csv isolinux/grubx64.efi --change-section-address .sbat=10000000

    # UEFI secure boot signing
    sbsign --key /certificates/db.key --cert /certificates/db.pem --output isolinux/grubx64.efi isolinux/grubx64.efi

    # create a FAT16 UEFI boot disk image containing the EFI bootloader
    (
        cd isolinux && \
        dd if=/dev/zero of=efiboot.img bs=1M count=10 && \
        mkfs.vfat -F 16 efiboot.img && \
        LC_CTYPE=C mmd -i efiboot.img certificates efi efi/boot && \
        LC_CTYPE=C mcopy -i efiboot.img /usr/lib/shim/shimx64.efi.signed.previous ::efi/boot/bootx64.efi && \
        LC_CTYPE=C mcopy -i efiboot.img /usr/lib/shim/mmx64.efi ::efi/boot/mmx64.efi && \
        LC_CTYPE=C mcopy -i efiboot.img ./grubx64.efi ::efi/boot/grubx64.efi && \
        LC_CTYPE=C mcopy -i efiboot.img /certificates/ca.cer ::certificates/
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
    /bin/bash -c "(find . -type f -print0 | xargs -0 md5sum | grep -v -e 'md5sum.txt' -e 'bios.img' -e 'efiboot.img' > md5sum.txt)"

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

