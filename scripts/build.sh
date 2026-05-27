#!/bin/bash

set -e                  # exit on error
set -o pipefail         # exit on pipeline error
set -u                  # treat unset variable as error

export SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

CMD=(setup_host debootstrap run_chroot build_iso)

# Fill in date var. Date and time are set to local time.
# This gets used in the naming of the generated iso.
# This way, each new generated iso will not overwrite a previous iso
# and versioning becomes easier because of the included date/time in the iso filename.
DATE=$(date +%Y%m%d-%H%M%S);

# This variable gets set by each part of the script (setup_host, debootstrap, run_chroot, build_iso)
# It is used in a status message upon a succesfull run of a part.
script_stage="unset"

# This function gets called when trap detects an exit.
# It calls chroot_exit_teardown to safely unmount eventual mount points in chroot.
function error_cleanup() {
    local exit_code=$?

    if (( exit_code != 0 )); then
        printf "Cleanup triggered (exit code: %s)\n" "${exit_code}"
    fi

    chroot_exit_teardown
}

function help() {
    # if $1 is set, use $1 as headline message in help()
    if [[ -z ${1+x} ]]; then
        printf "This script builds a bootable ubuntu ISO image\n\n"
    else
        printf "%s\n" "${1}"
    fi
    printf "Supported commands : %s\n\n" "${CMD[*]}"
    printf "Syntax: %s [start_cmd] [-] [end_cmd]\n" "${0}"
    printf "\trun from start_cmd to end_cmd\n"
    printf "\tif start_cmd is omitted, start from first command\n"
    printf "\tif end_cmd is omitted, end with last command\n"
    printf "\tenter single cmd to run the specific command\n"
    printf "\tenter '-' as only argument to run all commands\n\n"
    exit 0
}

function find_index() {
    local ret;
    local i;
    for ((i=0; i<${#CMD[*]}; i++)); do
        if [[ "${CMD[i]}" == "${1}" ]]; then
            index=${i};
            return;
        fi
    done
    help "Command not found : ${1}"
}

function chroot_enter_setup() {
    sudo mount --bind /dev chroot/dev
    sudo mount --bind /run chroot/run
    sudo chroot chroot mount none -t proc /proc
    sudo chroot chroot mount none -t sysfs /sys
    sudo chroot chroot mount none -t devpts /dev/pts
}

# First check if a path is mounted. If so, call umount.
# This prevents the script from stopping when a mount point does not exist.
function safe_umount() {
    local path="${1}"

    if mountpoint -q "${path}"; then
     	printf "Unmounting: %s\n" "${path}"
        sudo umount "${path}"
    fi
}

function chroot_exit_teardown() {
safe_umount "${SCRIPT_DIR}/chroot/dev/pts"
safe_umount "${SCRIPT_DIR}/chroot/dev"
safe_umount "${SCRIPT_DIR}/chroot/proc"
safe_umount "${SCRIPT_DIR}/chroot/sys"
safe_umount "${SCRIPT_DIR}/chroot/run"
}

function check_host() {
    local os_ver
    os_ver=$(lsb_release -i | grep -E "(Ubuntu|Debian)")
    if [[ -z "${os_ver}" ]]; then
        printf "WARNING : OS is not Debian or Ubuntu and is untested\n"
    fi

	# Check if the script is run by root and warn if so.
	# Running the script with sudo by a normal user (and also root) is allowed.
	if [[ "${EUID}" -eq 0 ]]; then
	    if [[ "${SUDO_COMMAND:-}" != *"${0##*/}"* ]]; then
	        printf "DO NOT RUN THIS SCRIPT FROM A ROOT SHELL.\n"
	        printf "Run it directly as a normal user or via sudo.\n"
	        exit 1
	    fi
	fi
}

# Load configuration values from file
function load_config() {
    if [[ -f "${SCRIPT_DIR}/config.sh" ]]; then
        . "${SCRIPT_DIR}/config.sh"
    elif [[ -f "${SCRIPT_DIR}/default_config.sh" ]]; then
        . "${SCRIPT_DIR}/default_config.sh"
    else
        >&2 printf "Unable to find default config file '%s/default_config.sh', aborting.\n" "${SCRIPT_DIR}"
        exit 1
    fi
}

# Verify that necessary configuration values are set and they are valid
function check_config() {
    local expected_config_version
    expected_config_version="0.5"

    if [[ "${CONFIG_FILE_VERSION}" != "${expected_config_version}" ]]; then
        >&2 printf "Invalid or old config version %s, expected %s. Please update your configuration file from the default.\n" "${CONFIG_FILE_VERSION}" "${expected_config_version}"
        exit 1
    fi
}

function setup_host() {
    printf "=====> running setup_host ...\n"
    script_stage="setup_host"
    sudo apt update
    sudo apt install -y debootstrap squashfs-tools xorriso
    sudo mkdir -p chroot
}

function debootstrap() {
	printf "=====> running debootstrap ... will take a couple of minutes ...\n"
	script_stage="debootstrap"
    sudo debootstrap --arch=amd64 --variant=minbase "${TARGET_UBUNTU_VERSION}" chroot "${TARGET_UBUNTU_MIRROR}"
}

# Run available hook scrips from directory in hooks
function run_hook_scripts() {
    hook_dir="${1}"

    # Don't mess up when pre_chroot is empty.
    shopt -s nullglob

    for hook in "${hook_dir}"/*.sh; do
    	printf "=====> running pre-chroot hook: %s\n" "$(basename "${hook}")"
        . "${hook}"
    done

    shopt -u nullglob
}

function run_chroot() {
    printf "=====> running run_chroot ...\n"
	script_stage="run_chroot"

	# Run pre_chroot hook scripts
	run_hook_scripts "${SCRIPT_DIR}/hooks/pre_chroot"

    chroot_enter_setup

    # Setup build scripts in chroot environment
    sudo ln -f "${SCRIPT_DIR}"/chroot_build.sh chroot/root/chroot_build.sh
    sudo ln -f "${SCRIPT_DIR}"/default_config.sh chroot/root/default_config.sh
    if [[ -f "${SCRIPT_DIR}/config.sh" ]]; then
        sudo ln -f "${SCRIPT_DIR}"/config.sh chroot/root/config.sh
    fi
    # Copy hook scripts to build enviroment
	sudo cp -afv "${SCRIPT_DIR}/hooks" "${SCRIPT_DIR}/chroot/tmp/" > /dev/null

    # Launch into chroot environment to build install image.
    sudo chroot chroot /usr/bin/env DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-readline}" /root/chroot_build.sh -

    # Cleanup after image changes
    sudo rm -f chroot/root/chroot_build.sh
    sudo rm -f chroot/root/default_config.sh
    if [[ -f "chroot/root/config.sh" ]]; then
        sudo rm -f chroot/root/config.sh
    fi

    chroot_exit_teardown
}

function build_iso() {
    printf "=====> running build_iso ...\n"
	script_stage="build_iso"

	# check for existance of chroot/image and ./image
 	# move image artifacts if they are still in the chroot directory
    if [[ -e chroot/image ]]; then
    	if [[ -e ./image ]]; then sudo rm -rf ./image; fi
    	sudo mv chroot/image .
    elif [[ ! -e ./image ]]; then
    	 printf "Error, image folder not found! Did run_chroot execute succesfully?\n"
    	 printf "Quitting...\n"
    	 exit 1
    fi

	# read mksquashfs compression type from config.sh and set options accordingly.
	case "${MKSQUASHFS_COMPRESSION}" in
    	xz)
    	    mksquashfs_comp_opts=(xz -b 1M -Xdict-size 100%)
        	;;
    	gzip)
        	mksquashfs_comp_opts=(gzip -b 1M)
        	;;
    	*)
        	printf "Wrong compression type set for mksquashfs!\nPlease edit config.sh and set an appropriate type.\n."
        	exit 1
        	;;
	esac

    # compress rootfs
    sudo mksquashfs chroot image/casper/filesystem.squashfs \
        -noappend -no-duplicates -no-recovery \
        -wildcards \
        -comp "${mksquashfs_comp_opts[@]}" \
        -e "var/cache/apt/archives/*" \
        -e "root/*" \
        -e "root/.*" \
        -e "tmp/*" \
        -e "tmp/.*" \
        -e "swapfile"

    # write the filesystem.size
    sudo du -sx --block-size=1 chroot | cut -f1 | sudo tee image/casper/filesystem.size >/dev/null

    pushd "${SCRIPT_DIR}"/image

    sudo xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -J -J -joliet-long \
        -volid "${TARGET_NAME}" \
        -output "${SCRIPT_DIR}/${TARGET_NAME}-${DATE}.iso" \
      -eltorito-boot isolinux/bios.img \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        --eltorito-catalog boot.catalog \
        --grub2-boot-info \
        --grub2-mbr ../chroot/usr/lib/grub/i386-pc/boot_hybrid.img \
        -partition_offset 16 \
        --mbr-force-bootable \
      -eltorito-alt-boot \
        -no-emul-boot \
        -e isolinux/efiboot.img \
        -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b isolinux/efiboot.img \
        -appended_part_as_gpt \
        -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
        -m "isolinux/efiboot.img" \
        -m "isolinux/bios.img" \
        -e '--interval:appended_partition_2:::' \
      -exclude isolinux \
      -graft-points \
         "/EFI/boot/bootx64.efi=isolinux/bootx64.efi" \
         "/EFI/boot/mmx64.efi=isolinux/mmx64.efi" \
         "/EFI/boot/grubx64.efi=isolinux/grubx64.efi" \
         "/EFI/ubuntu/grub.cfg=isolinux/grub.cfg" \
         "/isolinux/bios.img=isolinux/bios.img" \
         "/isolinux/efiboot.img=isolinux/efiboot.img" \
         "."

    popd
}

# =============   error trap  ==========

# This catches any kind of exit of the script,
# weither it is an error, ctrl+c or normal exit.
trap error_cleanup EXIT

# =============   main  ================

# we always stay in ${SCRIPT_DIR}
cd "${SCRIPT_DIR}"

load_config
check_config
check_host

# check number of args
if [[ ${#} == 0 || ${#} -gt 3 ]]; then help; fi

# loop through args
dash_flag=false
start_index=0
end_index=${#CMD[*]}
for ii in "${@}";
do
    if [[ ${ii} == "-" ]]; then
        dash_flag=true
        continue
    fi

    find_index "${ii}"
    if [[ ${dash_flag} == false ]]; then
        start_index=${index}
    else
        ((end_index = index + 1))
    fi
done
if [[ ${dash_flag} == false ]]; then
	((end_index = start_index + 1))
fi

#loop through the commands
for ((ii = start_index; ii < end_index; ii++)); do
    ${CMD[ii]}
    printf "\n\n%s - %s has finished!\n\n" "${0}" "${script_stage}"
done

if [[ ${script_stage} == "build_iso" ]]; then
	printf "Your live iso is ready and waiting at: %s/%s-%s.iso\n" "${SCRIPT_DIR}" "${TARGET_NAME}" "${DATE}"
fi

