# Build Scripts

## build.sh

```
This script builds a bootable ubuntu ISO image

Supported commands : setup_host debootstrap run_chroot build_iso

Syntax: ./build.sh [start_cmd] [-] [end_cmd]
	run from start_cmd to end_end
	if start_cmd is omitted, start from first command
	if end_cmd is omitted, end with last command
	enter single cmd to run the specific command
	enter '-' as only argument to run all commands
```

## How to Customize

1. Copy the `default_config.sh` file to `config.sh` in the scripts directory.
2. Make any necessary edits there, the script will pick up `config.sh` over `default_config.sh`.
3. If you need to copy some files to the chroot environment, you can put them in `chroot_files`. The directories
tree inside `chroot_files` will be reproduced inside chroot (files inside `chroot_files/tmp` will be cleanup).
/!\ `chroot_files/tmp` unix right's should be 1777

## How to Update

The configuration script is versioned with the variable CONFIG_FILE_VERSION.  Any time that the configuration
format is changed in `default_config.sh`, this value is bumped.  Once this happens `config.sh` must be updated manually
from the default file to ensure the new/changed variables are as desired.  Once the merge is complete the `config.sh` file's
CONFIG_FILE_VERSION should match the default and the build will run.
