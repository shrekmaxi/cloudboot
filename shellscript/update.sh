#!/bin/bash
# Fedora 10 

. /var/www/lighttpd/shellscript/config.sh

CONF_FNAME="cloudrainbow.conf"
CONF_FPATH="/var/$CONF_FNAME"
MPDIR="/mnt"
KERNELNAME="chaosvm"
INITRD="ramdisk.gz"
INFO="info"
VERSION="1.2"

_update(){
	MP=$1
	
	# try to touch the network first
	wget $WGETOPT "${BASEURL}/${INFO}" -O $MP/${INFO}
	if [ $? = 0 ];then
		echo "get update information done"
	else
		echo "could not connect to the update server" >&2
		return 1
	fi

	
	if [ -f $MP/${KERNELNAME} ]; then
		rm -f $MP/${KERNELNAME}.bak
	fi

	wget $WGETOPT "${BASEURL}/${KERNELNAME}" -O $MP/${KERNELNAME}.bak
	if [ $? = 0 ];then
		wget $WGETOPT  "${BASEURL}/${KERNELNAME}.md5" -O $MP/${KERNELNAME}.md5
		declare RMD5=`cat $MP/${KERNELNAME}.md5`
		declare LMD5=`md5sum $MP/${KERNELNAME}.bak | awk '{print $1}'`
		if [ "$RMD5" != "$LMD5" ];then
			rm -f $MP/${KERNELNAME}.bak;
			echo "Kernel update fail" >&2;
			return 1;
		fi
		echo "Kernel updated"
		mv $MP/${KERNELNAME} $MP/${KERNELNAME}.bak2
		mv $MP/${KERNELNAME}.bak $MP/${KERNELNAME}
		mv $MP/${KERNELNAME}.bak2 $MP/${KERNELNAME}.bak
	else
		rm -f $MP/${KERNELNAME}.bak
		echo "Kernel update fail" >&2
		return 1
	fi
	
	if [ -f $MP/${INITRD} ]; then
		rm -f $MP/${INITRD}.bak
	fi
	wget $WGETOPT  "${BASEURL}/${INITRD}" -O $MP/${INITRD}.bak

	if [ $? = 0 ];then
		# check md5
		wget $WGETOPT  "${BASEURL}/${INITRD}.md5" -O $MP/${INITRD}.md5
		declare RMD5=`cat $MP/${INITRD}.md5`
		declare LMD5=`md5sum $MP/${INITRD}.bak | awk '{print $1}'`
		if [ "$RMD5" != "$LMD5" ];then
			rm -f $MP/${INITRD}.bak;
			echo "application update fail" >&2;
			return 1;
		fi
		mv $MP/${INITRD} $MP/${INITRD}.bak2
		mv $MP/${INITRD}.bak $MP/${INITRD}
		mv $MP/${INITRD}.bak2 $MP/${INITRD}.bak
		echo "application updated"
	else
		rm -f $MP/${INITRD}.bak
		echo "application update fail" >&2
		return 1
	fi
	return 0
	
}

_mountandupdate(){
	declare PART=$1
	declare MP=$MPDIR/$PART
	mkdir -p $MP
	mount /dev/$PART $MP 2>/dev/null
	if [ "$?" = "0" ]; then
		if [ -f $MP/${KERNELNAME} ]; then
			_update $MP
			if [ $? = 0 ];then
				echo $PART
				umount $MP
				return 0
			else
				umount $MP
				return 1
			fi
		else
			return 1
		fi
	else
		return 1
	fi
}
_whateverudate(){
	declare PART=$1
	df -T 2>/dev/null | grep "^/dev/$PART " 
	if [ "$?" = "0" ]; then 
	# if the partition had been mounted, just save it
		declare MP=`df -T 2>/dev/null | grep "^/dev/$PART " | awk '{print $7}'`
		if [ -f $MP/${KERNELNAME} ]; then
			_update $MP
			if [ $? = 0 ];then
				echo $PART
				return 0
			else
				return 1
			fi
		else
			return 1
		fi
	else
	# try to mount it and save
		_mountandupdate $PART && return 0 || return 1
	fi
}

update()
{
	
	# mount the partition first
	#declare ALLDISKS=`fdisk -l 2>/dev/null | grep /dev | grep Disk | awk '{print $2}' | cut -c 6- | tr -d :`
	declare ALLDISKS=`fdisk -l 2>/dev/null| grep ":" | grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1`
	for DISK in $ALLDISKS; do
		for PART in `fdisk -l /dev/$DISK 2>/dev/null| grep ^/dev | tr -d \* |awk '{print $1}'| cut -c 6-`; do
			_whateverudate $PART && return 0 || continue
		done
	done
	return 1
}

usage()
{
  echo "usage: $1 [-h] baseurl"
  echo " version $VERSION: update cloudrainbow tool"
  echo "	-h print this message and exist"
  exit 1
}

if [ "$1" = "-h" ]; then
	usage $0
else
	
	test -n "$1" || usage
	export BASEURL=$1
	export WGETOPT="--tries=3 --wait=180 --connect-timeout=60 --timeout=60 -q" 
	update $1 && exit 0 || exit 1
fi
