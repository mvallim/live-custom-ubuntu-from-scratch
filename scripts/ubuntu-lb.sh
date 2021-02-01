#!/bin/bash
# This stuff was written by mki77/github.com

set -e # exit on error
set -o pipefail # exit on pipeline error
#set -x # print commands

pushd() {
    command pushd "$@" > /dev/null
}
popd() {
    command popd "$@" > /dev/null
    echo
}
RUN_DIR=$PWD
pushd "$PWD"

do_buildiso() {
    if [ ! -d filesystem/root ]; then
        echo "No bootstrap found. Do it:
sudo debootstrap --arch=amd64 --variant=minbase groovy filesystem http://archive.ubuntu.com/ubuntu/"; exit
#sudo debootstrap --arch=amd64 --variant=minbase bullseye $FS_DIR http://deb.debian.org/debian/"; exit
    fi
    ISO_NAME=`grep PRETTY_NAME filesystem/etc/os-release | sed s/^[^=]*=// | sed -e 's/^"//' -e 's/"$//'`
    ISO_VERS=`grep VERSION_CODE filesystem/etc/os-release | sed s/^[^=]*=//`
    ISO_FILE=$ISO_VERS-live-amd64.iso
    mkdir -p iso/{casper,isolinux}
    cd $RUN_DIR/iso; clear
    echo "Building: $ISO_NAME ($ISO_VERS)"
    # Compress filesystem.squashfs
    if [ $# = 0 ]; then
        mksquashfs ../filesystem casper/filesystem.squashfs \
            -noappend -no-duplicates -no-recovery \
            -wildcards \
            -e "var/cache/apt/archives/*" \
            -e "root/*" \
            -e "root/.*" \
            -e "tmp/*" \
            -e "tmp/.*" \
            -e "swapfile"
        printf $(du -sx --block-size=1 ../filesystem | cut -f1) > casper/filesystem.size
        chroot ../filesystem dpkg-query -W --showformat='${Package} ${Version}\n' > \
            casper/filesystem.manifest
        cp -f casper/filesystem.manifest casper/filesystem.manifest-desktop
        sed -i '/ubiquity/d' casper/filesystem.manifest-desktop
        sed -i '/casper/d' casper/filesystem.manifest-desktop
    fi
    # Add /boot images
    cp -f ../filesystem/boot/initrd.img-* casper/initrd
    cp -f ../filesystem/boot/vmlinuz-* casper/vmlinuz
    # Add GRUB menu to boot in EFI/UEFI mode
    cat <<EOF> isolinux/grub.cfg
search --set=root --file /isolinux/grub.cfg
insmod all_video
set default="0"
set timeout=10

menuentry "Start $ISO_NAME" {
linux /casper/vmlinuz boot=casper toram quiet splash ---
initrd /casper/initrd
}
menuentry "Start in safe mode" {
linux /casper/vmlinuz boot=casper nomodeset nopersistent toram quiet nosplash ---
initrd /casper/initrd
}
menuentry "Install $ISO_NAME" {
linux /casper/vmlinuz boot=casper only-ubiquity quiet splash ---
initrd /casper/initrd
}
menuentry "Integrity check" {
linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
initrd /casper/initrd
}
EOF
    # Create an EFI bootable GRUB image
    grub-mkstandalone \
        --format=x86_64-efi \
        --output=isolinux/bootx64.efi \
        --locales="" \
        --fonts="" \
        "boot/grub/grub.cfg=isolinux/grub.cfg"
    # Create a FAT16 boot disk image with EFI bootloader
    (cd isolinux && \
        dd if=/dev/zero of=efiboot.img bs=1M count=10 && \
        mkfs.vfat efiboot.img && \
        LC_CTYPE=C mmd -i efiboot.img efi efi/boot && \
        LC_CTYPE=C mcopy -i efiboot.img bootx64.efi ::efi/boot/
    ) &> /dev/null
    # Create a BIOS bootable GRUB image
    grub-mkstandalone \
        --format=i386-pc \
        --output=isolinux/core.img \
        --install-modules="linux16 linux normal iso9660 biosdisk memdisk search tar ls" \
        --modules="linux16 linux normal iso9660 biosdisk search" \
        --locales="" \
        --fonts="" \
        "boot/grub/grub.cfg=isolinux/grub.cfg"
    # Create a ISOLINUX image to boot in BIOS mode
    cat /usr/lib/grub/i386-pc/cdboot.img isolinux/core.img > isolinux/bios.img
    #find . -type f -print0 | xargs -0 md5sum | grep -v -e 'md5sum.txt' -e 'bios.img' -e 'efiboot.img' > md5sum.txt
    # Write ISO file
    xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "$ISO_NAME" \
        -eltorito-boot boot/grub/bios.img \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        --eltorito-catalog boot/grub/boot.cat \
        --grub2-boot-info \
        --grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
        -eltorito-alt-boot \
        -e EFI/efiboot.img \
        -no-emul-boot \
        -append_partition 2 0xef isolinux/efiboot.img \
        -output "../$ISO_FILE" \
        -m "isolinux/efiboot.img" \
        -m "isolinux/bios.img" \
        -graft-points \
           "/EFI/efiboot.img=isolinux/efiboot.img" \
           "/boot/grub/bios.img=isolinux/bios.img" \
           "."
}

do_mount() {
    pushd $PWD/filesystem
    # mount filesystem
    mount --bind /dev dev
    mount --bind /run run
    mount --bind /sys sys
    # use local cache
    mkdir -p var/cache/apt/archives
    mount --bind /var/cache/apt/archives var/cache/apt/archives
    # make sure to remove any mountpoint at exit
    trap 'do_umount' EXIT
    #cp -f /etc/resolv.conf etc/resolv.conf
    #cp -f /etc/hosts etc/hosts
}
do_umount() {
    umount -l $(grep $PWD /etc/mtab | cut -d " " -f2) 2> /dev/null
}

do_chroot() {
    do_mount
    cat <<EOF> tmp/chroot.sh
#!/bin/bash
export HOME=/root
export LC_ALL=C
mount none -t devpts /dev/pts
mount none -t proc /proc
mount none -t sysfs /sys
mount --bind /etc/skel /root
clear
echo "Type 'exit' to quit this chroot.
"
/bin/bash
EOF
    chroot $PWD bash tmp/chroot.sh
}

do_xnest() {
    do_mount
    for f in usr/share/xsessions/*; do
        XEXEC=`grep -E '\<Exec=' "$f" | cut -c6-`
        #XLIST+="${XEXEC##*/},"
        if [[ ${#1} > 2 && "$XEXEC" =~ "$1" ]]; then break; fi
    done
    #cat> tmp/xnest.sh <<EOF
    cat <<EOF> tmp/xnest.sh
#!/bin/bash

export HOME=/root
export LC_ALL=C
export DISPLAY=:2
#export DISPLAY=localhost:2
#export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):2
#locale-gen en_US.UTF-8

mount none -t devpts /dev/pts
mount none -t proc /proc
mount none -t sysfs /sys
mount --bind /etc/skel /root
# uncomment to fix keyboard and mouse input
#chmod 1777 /dev/shm/

# dbus fixes
apt install -y dbus-x11
mount --bind /run /var/run
mount --bind /run/lock /var/lock
rm /var/run/dbus/pid
dbus-uuidgen --ensure
dbus-daemon --system

$XEXEC
echo "killed"
EOF
    xhost +local:
    Xephyr -ac -br -reset -screen 800x600 :2 & \
        chroot $PWD bash tmp/xnest.sh 2> tmp/xnest.log
    #|| killall Xephyr; sleep 1
}

do_extract() {
    ISO_FILE=$1
    ISO_DIR=$RUN_DIR/`basename "${ISO_FILE%.iso}"`
    ISO_DIR=${ISO_DIR// /\-}
    mkdir -p "$ISO_DIR/filesystem"
    mkdir -p /media/iso
    mount -t iso9660 -o loop "$ISO_FILE" /media/iso
    trap ' umount -l /media/iso' EXIT
    clear
    echo "Extracting: ${ISO_FILE##*/}"
    unsquashfs -f -d "$ISO_DIR/filesystem" $(find /media/iso -name *.squashfs)
    rsync -at --exclude *.squashfs /media/iso "$ISO_DIR"
    echo
    #chmod a+rw -R $ISO_DIR/iso
    #cd iso; unsquashfs -f -d ../filesystem $(find -name *.squashfs)
}

do_rebuild() {
    cd $RUN_DIR/iso
    ISO_NAME=`grep PRETTY_NAME ../filesystem/etc/os-release | sed s/^[^=]*=// | sed -e 's/^"//' -e 's/"$//'`
    ISO_VERS=`grep VERSION_CODE ../filesystem/etc/os-release | sed s/^[^=]*=//`
    ISO_FILE=$ISO_VERS-amd64.iso
    genisoimage -J -l -r \
        -c $(find -name boot.cat | cut -c3-;) \
        -b $(find -name *linux.bin | cut -c3-;) \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot \
        -e $(find -name efi*.img | cut -c3-;) \
        -no-emul-boot \
        -V "$ISO_NAME" \
        -o "../$ISO_FILE" .
    isohybrid --uefi "../$ISO_FILE"
}

if [[ $(id -u) != 0 ]]; then
    sudo -p 'Restarting as root, password: ' bash $0 "$@"
    exit $?
fi
case "$1" in
    -b|build) do_buildiso $2;;
    -c|chroot) do_chroot;;
    -x|xroot) do_xnest $2;;
    -e) do_extract $2;;
    -r) do_rebuild ;;
    -i) chmod +x "$0"; cp -vf "$0" /usr/local/bin/${0%.sh};
        apt install -y grub-pc-bin grub-efi-amd64-bin xorriso squashfs-tools \
        genisoimage syslinux-utils xserver-xephyr;;
    -h|--help) echo "This script builds bootstrap environment.
-b|build    Build ISO image
-c|chroot   Enter the chroot
-x|xroot    Run an X server";;
esac

