#!/bin/bash

# Optional automated locale generation so script can run unattended.
if [[ "${TARGET_LOCALES_AUTOMATE}" == "1" ]]; then
	printf "LOCALES ARE CONFIGURED AUTOMATICALLY!\n"
   	echo "${TARGET_LOCALES_GENERATE}" > /etc/locale.gen
	debconf-set-selections <<EOF
locales locales/default_environment_locale select ${TARGET_LOCALES_DEFAULT}
locales locales/locales_to_be_generated multiselect ${TARGET_LOCALES_GENERATE}
EOF

	DEBIAN_FRONTEND=noninteractive apt-get install -y locales
	locale-gen
	update-locale LANG="${TARGET_LOCALES_DEFAULT}"
else
 	apt-get install locales -y
 	dpkg-reconfigure locales
fi


# Optional automated keyboard configuration so script can run unattended.
if [[ "${TARGET_KEYBOARD_AUTOMATE}" == "1" ]]; then
	printf "KEYBOARD IS CONFIGURED AUTOMATICALLY!\n"
	debconf-set-selections <<EOF
keyboard-configuration keyboard-configuration/modelcode string ${TARGET_KEYBOARD_MODEL}
keyboard-configuration keyboard-configuration/layoutcode string ${TARGET_KEYBOARD_LAYOUT}
keyboard-configuration keyboard-configuration/variantcode string ${TARGET_KEYBOARD_VARIANT}
keyboard-configuration keyboard-configuration/optionscode string ${TARGET_KEYBOARD_OPTIONS}
EOF

	DEBIAN_FRONTEND=noninteractive apt-get install -y keyboard-configuration
else
	apt-get install -y keyboard-configuration
fi


# Optional automated console setup so script can run unattended.
if [[ "${TARGET_CONSOLE_AUTOMATE}" == "1" ]]; then
	printf "CONSOLE IS CONFIGURED AUTOMATICALLY!\n"
	debconf-set-selections <<EOF
console-setup console-setup/charmap47 select ${TARGET_CONSOLE_CHARMAP}
console-setup console-setup/codeset47 select ${TARGET_CONSOLE_CODESET}
EOF
	DEBIAN_FRONTEND=noninteractive apt-get install -y console-setup
else
	apt-get install -y console-setup
fi
