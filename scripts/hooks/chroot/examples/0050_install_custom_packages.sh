#!/bin/bash

# This example script shows how to install some extra packages in the livecd.

# install graphics and desktop
apt-get install -y \
	plymouth-themes \
	ubuntu-gnome-desktop \
	ubuntu-gnome-wallpapers

# useful tools
apt-get install -y \
	clamav-daemon \
	terminator \
	apt-transport-https \
	curl \
	vim \
	nano \
	less

# purge
apt-get purge -y \
	transmission-gtk \
	transmission-common \
	gnome-mahjongg \
	gnome-mines \
	gnome-sudoku \
	aisleriot \
	hitori
