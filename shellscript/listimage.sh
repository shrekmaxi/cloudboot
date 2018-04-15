#!/bin/bash

. /var/www/lighttpd/shellscript/config.sh
. /var/www/lighttpd/shellscript/include.sh

if [ $# != 3 ]; then
  
  echo "Usage:"
  echo "  $0 ftpuser ftppassword ftpserver"
  exit 1

fi
FTPUSER=$1
FTPPASS=$2
FTPSERVERIP=$3
FTPPATH=$FTPTPLPATH

lftp $FTPUSER:$FTPPASS@$FTPSERVERIP -e "cd $FTPPATH; ls; quit;" 2>/dev/null | grep img$ | awk '{print $9}'

