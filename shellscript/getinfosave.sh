#!/bin/bash
# Fedora 10 

ifconfig > /var/ifconfig.info
route -n > /var/route.info

#declare ALLDISKS=`fdisk -l 2>/dev/null | grep /dev | grep Disk | awk '{print $2}' | cut -c 6- | tr -d :`
declare ALLDISKS=`fdisk -l 2>/dev/null| grep ":" | grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1`
for DISK in $ALLDISKS; do
    for PART in `fdisk -l /dev/$DISK 2>/dev/null| grep ^/dev | tr -d \* |awk '{print $1}'| cut -c 6-`; do
        mount /dev/$PART /mnt
        cp /var/ifconfig.info /mnt/ifconfig.info
        cp /var/route.info    /mnt/route.info
        umount /mnt       
    done
done


