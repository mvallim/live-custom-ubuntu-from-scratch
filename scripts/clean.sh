#!/bin/bash

sudo umount ./chroot/sys || sudo umount -lf ./chroot/sys || true
sudo umount ./chroot/proc || sudo umount -lf ./chroot/proc || true
sudo umount ./chroot/dev || sudo umount -lf ./chroot/dev || true
sudo umount ./chroot/run || sudo umount -lf ./chroot/run || true
sudo rm -rf ./chroot || true
sudo rm -rf ./image || true
