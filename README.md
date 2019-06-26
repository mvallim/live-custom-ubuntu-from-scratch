# Live custom Ubuntu from scratch

## Prerequisites (GNU/Linux Debian/Ubuntu)

Install applications we need to build the environment.

```
sudo apt-get install \
    debootstrap \
    squashfs-tools \
    genisoimage \
    syslinux \
    isolinux
```

```
mkdir $HOME/live-ubuntu-from-scratch
```

## Bootstrap and Configure Ubuntu
```
sudo debootstrap \
    --arch=amd64 \
    --variant=minbase \
    bionic \
    $HOME/live-ubuntu-from-scratch/chroot \
    http://us.archive.ubuntu.com/ubuntu/
```

```
sudo mount --bind /dev $HOME/live-ubuntu-from-scratch/chroot/dev

sudo mount --bind /run $HOME/live-ubuntu-from-scratch/chroot/run
```

```
sudo chroot $HOME/live-ubuntu-from-scratch/chroot
```

```
mount none -t proc /proc

mount none -t sysfs /sys

mount none -t devpts /dev/pts

export HOME=/root

export LC_ALL=C
```

## Set a custom hostname
```
echo "ubuntu-live" > /etc/hostname
```

## Configure apt sources.list

Edit /etc/apt/source.list

```
cat <<EOF > /etc/apt/sources.list
deb http://us.archive.ubuntu.com/ubuntu/ bionic main restricted universe multiverse 

deb http://us.archive.ubuntu.com/ubuntu/ bionic-security main restricted universe multiverse 

deb http://us.archive.ubuntu.com/ubuntu/ bionic-updates main restricted universe multiverse 
EOF
```

## Upgrade packages if you want
```
apt-get update

apt-get -y upgrade
```

## Install and configure dbus
```
apt-get install -y systemd-sysv

apt-get install -y dbus
```

```
dbus-uuidgen > /var/lib/dbus/machine-id

dpkg-divert --local --rename --add /sbin/initctl

ln -s /bin/true /sbin/initctl
```

## Install packages needed for Live System
```
apt-get install -y \
    ubuntu-standard \
    casper \
    lupin-casper \
    discover \
    laptop-detect \
    os-prober \
    network-manager \
    linux-generic
```

## Graphical installer
```
apt-get install -y \
    ubiquity \
    ubiquity-casper \
    ubiquity-frontend-gtk \
    ubiquity-slideshow-ubuntu \
    ubiquity-ubuntu-artwork
```

## Install window manager
```
apt-get install -y \
    plymouth-theme-ubuntu-gnome-logo \
    ubuntu-gnome-desktop \
    ubuntu-gnome-wallpapers
```

## Install usefull applications
```
apt-get install -y \
    clamav-daemon \
    terminator \
    apt-transport-https \
    curl \
    vim \
    nano
```

## Install Visual Studio Code

1. Download and install the key 
   ```
   curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg

   install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
   
   echo "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list

   rm microsoft.gpg
   ```

2. Then update the package cache and install the package using:
   ```
   apt-get update
   
   apt-get install -y code
   ```

## Install Google Chrome

1. Download and install the key 
   ```
   wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   ```

2. Add the key to the repository
   ```
   echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
   ```

3. Finally, Update repository and install Google Chrome.
   ```
   apt-get update

   apt-get install google-chrome-stable
   ```

## Install Java JDK 8
```
apt-get install -y \
    openjdk-8-jdk \
    openjdk-8-jre
```

## Remove unused applications
```
apt-get purge -y \
    transmission-gtk \
    transmission-common \
    gnome-mahjongg \
    gnome-mines \
    gnome-sudoku \
    aisleriot \
    hitori
```

## Remove unused packages
```
apt-get autoremove -y
```

## Cleanup the chroot environment

1. If you installed software, be sure to run
   ```
   rm /var/lib/dbus/machine-id
   ```

2. Remove the diversion
   ```
   rm /sbin/initctl

   dpkg-divert --rename --remove /sbin/initctl
   ```

3. Clean up
   ```
   apt-get clean

   rm -rf /tmp/*

   rm /etc/resolv.conf

   umount /proc
   
   umount /sys
   
   umount /dev/pts
   
   exit
   ```

4. Unbind mount points
   ```
   sudo umount $HOME/live-ubuntu-from-scratch/chroot/dev

   sudo umount $HOME/live-ubuntu-from-scratch/chroot/run
   ```

## Create the CD image directory and populate it

1. Access build directory
   ```
   cd $HOME/live-ubuntu-from-scratch
   ```

2. Create directories
   ```
   mkdir -p image/{casper,isolinux,install}
   ```

2. Copy kernel images
   ```
   sudo cp chroot/boot/vmlinuz-**-**-generic image/casper/vmlinuz

   sudo cp chroot/boot/initrd.img-**-**-generic image/casper/initrd.gz
   ```

3. Copy isolinux and memtest binaries
   ```
   sudo cp /usr/lib/ISOLINUX/isolinux.bin image/isolinux/

   sudo cp /usr/lib/syslinux/modules/bios/ldlinux.c32 image/isolinux/

   sudo cp chroot/boot/memtest86+.bin image/install/memtest
   ```
