#!/bin/bash
DISK=`fdisk -l 2>/dev/null| grep ":" | grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1`
PATCHPATH="/var/www/lighttpd/patch"
dd if=/dev/$DISK of=$PATCHPATH/patch.img bs=1 skip=440 count=4
dd if=/dev/$DISK of=$PATCHPATH/patch.img bs=1 skip=466 seek=4 count=1

cd /var/www/lighttpd/
tar -czvf  patch.tar.gz ./patch/
mv patch.tar.gz /var/

if [ -f /var/patch.tar.gz ]; then
    echo "make patch success"
else
    echo "make patch fail"
fi
