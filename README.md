# WIP building tools for the PrivOS distribution project

![Logo](https://raw.githubusercontent.com/polkaulfield/privOS-builder/refs/heads/24.04/images/banner.png)

This is a project to create a privacy-first Ubuntu derivative as a learning experience by some 42-Barcelona students.
Now everything is an extremely experimental weekend project, but it will keep improving.

## Features:
* Heavily debloated Ubuntu 24.04 with a minimal KDE Plasma session
* Replaced snaps with flatpaks
* Added NVIDIA installer script that fixes the [sleep/hybernate issues](https://gist.github.com/bmcbm/375f14eaa17f88756b4bdbbebbcfd029)
* Added a [fix for the buggy USB file transfer](https://codeberg.org/wonky/arch-udev-usb-sync) that plagues most distros
* [Preconfigured](https://forum.qubes-os.org/t/set-custom-preferences-for-brave-browser-in-disposable-qube/27351) Brave Browser from the official signed repos (Disabled telemetry and annoying features, a bit of hardening and disabled WebRTC leaks)
* Tor Browser
* Signal preinstalled with the official signed repos
* [MAC Address randomization](https://wiki.archlinux.org/title/NetworkManager#Configuring_MAC_address_randomization)
* [Base Mullvad DNS](https://mullvad.net/en/help/dns-over-https-and-dns-over-tls#linux) with TLS. Blocks ads, malware and trackers system-wide
* Hardened the default home permissions from 755 to 700 so only users can access their files.
* Disabled IPv6 support systemwide
* Disabled CUPS and Avahi services. [They are known for being exploited a lot](https://gist.github.com/FlyingFathead/880238cb2ecb4f64d81a2c4e5600511a)

## Screenshot
![Screenshot](https://raw.githubusercontent.com/polkaulfield/privOS-builder/refs/heads/24.04/images/privos.png)

## Downloads:
For now, you can try the latest developments getting the ISO images from [Github Actions](https://github.com/polkaulfield/privOS-builder/actions)

## Todo:
* Make the system [CIS Workstation Compliant](https://www.cisecurity.org/benchmark/ubuntu_linux) using openscap
* Document all the network connections
* Set up an outbound firewall with sane defaults that prompts the user when some connection isn't recognized.
* And a lot more...
