#!/bin/bash
DISK=/dev/$1

#test "$1" = "" && exit 1

set -x
dd of=${DISK}  if=/var/www/lighttpd/shellscript/random seek=38 bs=512  count=1 
sync;sync;sync;

sleep 5
set -x

reboot -f
