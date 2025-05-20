# WIP building tools for the PrivOS distribution project

![Logo](https://raw.githubusercontent.com/polkaulfield/privOS-builder/refs/heads/25.04/images/banner.png)

This is a project to create a privacy-first Ubuntu derivative as a learning experience by some 42-Barcelona students.
Now everything is an extremely experimental weekend project, but it will keep improving.

![Screenshot](https://raw.githubusercontent.com/polkaulfield/privOS-builder/refs/heads/25.04/images/privos.png)

## Features:
* Heavily debloated Ubuntu 25.04 with a minimal Plasma session
* Replaced snaps with flatpaks
* [Preconfigured](https://forum.qubes-os.org/t/set-custom-preferences-for-brave-browser-in-disposable-qube/27351) Brave Browser from the official signed repos (Disabled telemetry and annoying features, a bit of hardening and disabled WebRTC leaks)
* Signal preinstalled with the official signed repos
* [MAC Address randomization](https://wiki.archlinux.org/title/NetworkManager#Configuring_MAC_address_randomization)
* [Base Mullvad DNS](https://mullvad.net/en/help/dns-over-https-and-dns-over-tls#linux) with TLS. Blocks ads, malware and trackers system-wide
* Disabled IPv6 support systemwide

## Todo:
* More security hardening
* Document network connections and switch everything to privacy respecting alternatives
* OpenSnitch outbound firewall with sane defaults
* Replace AppArmor with SElinux
* And a lot more...