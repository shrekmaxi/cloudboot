#!/bin/bash

# get disk name (sda? hda?)
#declare SYSDISKNAME=`fdisk -l| grep 'Disk /dev/.d.'|awk '{print $2}'|cut -c 6-8 | head -1`
declare SYSDISKNAME=`fdisk -l 2>/dev/null| grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|head -1|awk '{print $2}'|cut -c 6-|cut -d: -f1`

#backup files to runtime
mkdir /tmp/mnt2

mount /dev/${SYSDISKNAME}1 /tmp/mnt2
cp /tmp/mnt2/cloudrainbow.conf /var/cloudrainbow.conf
umount /tmp/mnt2

#install cloudboot
/var/www/lighttpd/shellscript/install.sh $SYSDISKNAME force

#recover files to cloudboot partitios of disk
mount /dev/${SYSDISKNAME}1 /tmp/mnt2
mkdir /tmp/mnt2/var
cp /var/cloudrainbow.conf /tmp/mnt2/var/cloudrainbow.conf
umount /tmp/mnt2




