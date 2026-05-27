#!/bin/bash
# base netplan config to make interfaces work
    cat <<EOF > /etc/netplan/01-network-manager-all.yaml
# Let NetworkManager manage all devices on this system.
# For more information, see netplan(5).
network:
  version: 2
  renderer: NetworkManager
EOF
