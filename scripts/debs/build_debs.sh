#!/bin/sh

for DIR in $(find . -maxdepth 1 -mindepth 1 -type d ); do
     dpkg-deb --root-owner-group --build $DIR $DIR.deb
done
