#!/bin/bash

# This script provides common customization options for the ISO
#
# Usage: Copy this file to config.sh and make changes there.  Keep this file (default_config.sh) as-is
#   so that subsequent changes can be easily merged from upstream.  Keep all customiations in config.sh

# The version of Ubuntu to generate.  Successfully tested LTS: bionic, focal, jammy, noble, plucky
# See https://wiki.ubuntu.com/DevelopmentCodeNames for details
export TARGET_UBUNTU_VERSION="noble"

# The Ubuntu Mirror URL. It's better to change for faster download.
# More mirrors see: https://launchpad.net/ubuntu/+archivemirrors
export TARGET_UBUNTU_MIRROR="https://archive.ubuntu.com/ubuntu"

# The packaged version of the Linux kernel to install on target image.
# See https://wiki.ubuntu.com/Kernel/LTSEnablementStack for details
export TARGET_KERNEL_PACKAGE="linux-generic"

# The file (no extension) of the ISO containing the generated disk image,
# the volume id, and the hostname of the live environment are set from this name.
export TARGET_NAME="PrivOS"

# The text label shown in GRUB for booting into the live environment
export GRUB_LIVEBOOT_LABEL="Try PrivOS without installing"

# The text label shown in GRUB for starting installation
export GRUB_INSTALL_LABEL="Install PrivOS"

# Packages to be removed from the target system after installation completes succesfully
export TARGET_PACKAGE_REMOVE="
	ubiquity \
	ubiquity-casper \
	ubiquity-frontend-gtk \
	casper \
	discover \
	laptop-detect \
	os-prober \
"

function branding() {
	sed -i 's/NAME="[^"]*"/NAME="PrivOS"/g' /etc/os-release
}

function add_brave() {
	apt install curl
	curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list
	apt update
	sudo apt install -y brave-browser
}

function add_signal() {
	wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg;
	cat signal-desktop-keyring.gpg | tee /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null
	rm signal-desktop-keyring.gpg
	echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\
	  tee /etc/apt/sources.list.d/signal-xenial.list
	apt update
	apt install -y signal-desktop
}

function add_mullvad_browser()
{
	curl -fsSLo /usr/share/keyrings/mullvad-keyring.asc https://repository.mullvad.net/deb/mullvad-keyring.asc
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/mullvad-keyring.asc] https://repository.mullvad.net/deb/stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/mullvad.list
	apt update
	apt install -y mullvad-browser
}

function remove_snaps() {
	while [ "$(snap list | wc -l)" -gt 0 ]; do
		   for snap in $(snap list | tail -n +2 | cut -d ' ' -f 1); do
			   snap remove --purge "$snap" 2> /dev/null || true
		   done
	   done

	   systemctl stop snapd
	   systemctl disable snapd
	   systemctl mask snapd
	   apt purge snapd -y
	   rm -rf /snap /var/lib/snapd
	   for userpath in /home/*; do
		   rm -rf $userpath/snap
	   done
	   cat <<-EOF | tee /etc/apt/preferences.d/nosnap.pref
	Package: snapd
	Pin: release a=*
	Pin-Priority: -10
	EOF
}

function install_desktop() {
	apt-get install -y \
		plymouth-theme-spinner \
		xserver-xorg-video-all \
		xserver-xorg-input-all \
		xserver-xorg-core \
		xinit \
		x11-xserver-utils \
		plasma-desktop \
		plasma-discover \
		plasma-nm \
		sddm \
		sddm-theme-breeze \
		software-properties-qt
}

function install_apps() {
	apt-get install -y \
		dolphin \
		konsole \
		synaptic \
		vlc \
		qbittorrent \
		kde-spectacle \
		ark \
		okular \
		gwenview \
		keepassxc \
		kcalc \
		torbrowser-launcher \
		kate
}

function install_firewall() {
	apt-get install -y \
		plasma-firewall \
		ufw
	systemctl enable ufw.service
}

function install_extras() {
	apt-get install -y \
		unrar \
		p7zip
}

function cli_tools() {
	apt-get install -y \
		git \
		vim \
		nano \
		bash-completion \
		man \
		man-db \
		htop \
		net-tools \
		less
}

function add_flatpak() {
	apt-get install -y \
		flatpak \
		plasma-discover-backend-flatpak \
		kde-config-flatpak
	flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
}

function disable_cups()
{
	systemctl disable cups.service cups-browsed.service cups.socket cups.path
	systemctl mask cups.service cups-browsed.service cups.socket cups.path
}

function disable_avahi()
{
	systemctl disable avahi-daemon.service avahi-daemon.socket
	systemctl mask avahi-daemon.service avahi-daemon.socket
}

function remove_packages()
{
	apt purge -y \
		apport \
		gnome-keyring \
		ubuntu-pro-client \
		zutty
	apt autoremove -y

}

function install_debs()
{
	for DEB in $(find /tmp/debs/ -maxdepth 1 -type f -iname "*deb"); do
		apt install -y $DEB
	done
}

function harden_umask()
{
	sed -i 's/^HOME_MODE.*/HOME_MODE\t0700/g' /etc/login.defs
}

function cleanup() {
	rm -rf /tmp/* ~/.bash_history
	export HISTSIZE=0
}

# Package customisation function.  Update this function to customize packages
# present on the installed system.
function customize_image() {
	install_desktop
	install_apps
	cli_tools
	remove_snaps
	add_flatpak
	add_brave
	add_signal
	#add_mullvad_browser
	install_debs
	#disable_cups
	disable_avahi
	install_firewall
	remove_packages
	harden_umask
	branding
	cleanup
}

# Used to version the configuration.  If breaking changes occur, manual
# updates to this file from the default may be necessary.
export CONFIG_FILE_VERSION="0.4"
