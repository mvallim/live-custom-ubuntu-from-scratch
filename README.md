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

## Configure apt sources.list and update

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
apt-get install -y ubuntu-standard casper lupin-casper

apt-get install -y laptop-detect os-prober

apt-get install -y linux-generic
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