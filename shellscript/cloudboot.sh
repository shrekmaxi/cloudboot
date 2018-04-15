#!/bin/bash
usage()
{
	echo "usage: cloudboot.sh disk|cgi"
	echo "defined boot to cgi or boot to disk"
	exit 1
}

if [ "$1" = "disk" ]; then
	bash /var/www/lighttpd/shellscript/bootdisk.sh &
	exit 0
elif [ "$1" = "cgi" ]; then
	bash /var/www/lighttpd/shellscript/bootcgi.sh &
	exit 0
else 
	usage
fi
