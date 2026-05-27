# Build Scripts

## build.sh

```console
This script builds a bootable ubuntu ISO image

Supported commands : setup_host debootstrap run_chroot build_iso

Syntax: ./build.sh [start_cmd] [-] [end_cmd]
  run from start_cmd to end_cmd
  if start_cmd is omitted, start from first command
  if end_cmd is omitted, end with last command
  enter single cmd to run the specific command
  enter '-' as only argument to run all commands
```

## How to Customize

1. Copy the `default_config.sh` file to `config.sh` in the scripts directory.
2. Make any necessary edits there, the script will pick up `config.sh` over `default_config.sh`.

One must, at the very least, edit TARGET_UBUNTU_VERSION and set it to an Ubuntu distribution codename, i.e. 'focal' or 'resolute'.
Please see the configuration file for more options.

## Automation
It is possible to automate the setup of locales, keyboard and console.
The script can run fully unattended when using these automation options
and will no longer stop to ask you about locales, keyboard and console configuration.
This can be set in the config file. Please see the entries in the automation section for more information.

## How to Update

The configuration script is versioned with the variable CONFIG_FILE_VERSION.  Any time that the configuration
format is changed in `default_config.sh`, this value is bumped.  Once this happens `config.sh` must be updated manually
from the default file to ensure the new/changed variables are as desired.  Once the merge is complete the `config.sh` file's
CONFIG_FILE_VERSION should match the default and the build will run.


## How to use hook scripts

This version of the live-custom-ubuntu-from-scratch script has the ability to use hook files.
These hook files can greatly extend the functionality of the build script.

These files get called right before the chroot is set up and entered
and during the chroot stage of the script, after all default packages have been installed.

They are located in hooks/pre_chroot/ and hooks/chroot/.
They are called 0000_script_name.sh. The number determines the order which they are run in and the names should be
descriptive of the functionality of the hook script.

One can use these script to do all kinds of neat stuff, like copying some configuration files to the chroot
or installing additional packages in the chroot.

There already are a few hook scripts in hooks/chroot. They are used during the default live iso creation process.
You can edit them but it would be wise not to remove them, you would end up with a dysfunctional iso if you do so.

Please see the example scripts, included in hooks/examples to get some idea of what is possible with the hook scripts.
