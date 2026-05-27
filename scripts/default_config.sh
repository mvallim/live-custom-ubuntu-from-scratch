#!/bin/bash

# This script provides common customization options for the ISO
#
# Usage: Copy this file to config.sh and make changes there.  Keep this file (default_config.sh) as-is
#   so that subsequent changes can be easily merged from upstream.  Keep all customiations in config.sh

# The version of Ubuntu to generate.  Successfully tested LTS: bionic, focal, jammy, noble, resolute
# See https://wiki.ubuntu.com/DevelopmentCodeNames for details
export TARGET_UBUNTU_VERSION="resolute"

# The Ubuntu Mirror URL. It's better to change for faster download.
# More mirrors see: https://launchpad.net/ubuntu/+archivemirrors
export TARGET_UBUNTU_MIRROR="http://us.archive.ubuntu.com/ubuntu/"

# The packaged version of the Linux kernel to install on target image.
# See https://wiki.ubuntu.com/Kernel/LTSEnablementStack for details
export TARGET_KERNEL_PACKAGE="linux-generic"

# The file (no extension) of the ISO containing the generated disk image,
# the volume id, and the hostname of the live environment are set from this name.
export TARGET_NAME="ubuntu-from-scratch"

# The text label shown in GRUB for booting into the live environment
export GRUB_LIVEBOOT_LABEL="Try Ubuntu FS without installing"

# The text label shown in GRUB for starting installation
export GRUB_INSTALL_LABEL="Install Ubuntu FS"

# You can set mksquashfs compression to either 'gzip' or 'xz'.
# Use xz for final images. use gzip to quickly create a test iso for your customized ubuntu.
export MKSQUASHFS_COMPRESSION="xz"

# Used to version the configuration.  If breaking changes occur, manual
# updates to this file from the default may be necessary.
export CONFIG_FILE_VERSION="0.5"


#####################################################
#     optional automation for unattended builds     #
#####################################################

# Should locales be set and generated automatically?
# If set to 1, please configure locale settings below.
export TARGET_LOCALES_AUTOMATE="0"

# Set the default locale and the locales that should be automatically generated.
# Please see /usr/share/i18n/SUPPORTED on your system for a full list of locales.
# or use a search engine online to see what locales you need for your language.
export TARGET_LOCALES_DEFAULT="en_US.UTF-8"
export TARGET_LOCALES_GENERATE="en_US.UTF-8 UTF-8"

# Should keyboard be set up automatically?
# If set to 1, please configure keyboard settings below.
export TARGET_KEYBOARD_AUTOMATE="0"

# This configures the automatically used keyboard model, layout, variant and options.
export TARGET_KEYBOARD_MODEL="pc105"
export TARGET_KEYBOARD_LAYOUT="us"
export TARGET_KEYBOARD_VARIANT="intl"
export TARGET_KEYBOARD_OPTIONS=""

# Should console be set up automatically?
# If set to 1, please configure console settings below.
export TARGET_CONSOLE_AUTOMATE="0"

# This configures the automatically used console character map and codeset.
export TARGET_CONSOLE_CHARMAP="UTF-8"
export TARGET_CONSOLE_CODESET="Latin1 and Latin5"


####### !! NOTICE !! #######
# function customize_image has been moved to a chroot hook script.
# export TARGET_PACKAGE_REMOVE has been moved to a chroot hook script also.
# Please see the files in hooks/chroot and edit them there.
