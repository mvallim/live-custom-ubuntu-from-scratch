# WIP building tools for the PrivOS project, based on the awesome work by [live-custom-ubuntu-from-scratch](https://github.com/mvallim/live-custom-ubuntu-from-scratch)

![Screenshot](https://github.com/polkaulfield/privOS-builder/blob/master/images/privos.png)

This is a project to create a privacy-first Ubuntu derivative as a learning experience by some 42-Barcelona students.
Now everything is an extremely experimental weekend project, but it will keep improving.

## Features:
* Heavily debloated Ubuntu 25.04 with a minimal Plasma session
* Replaced snaps with flatpaks
* Preconfigured Brave Browser from the official signed repos (Disabled telemetry and annoying features, a bit of hardening)
* Signal preinstalled with the official signed repos

## Todo:
* Security hardening
* Hosts lists to block malware, phishing and scam sites systemwide
* Document network connections and switch everything to privacy respecting alternatives
* Improved NVIDIA support
* OpenSnitch outbound firewall with sane defaults
* Replace AppArmor with SElinux
* And a lot more...