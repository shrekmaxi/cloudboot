#!/bin/bash
# Fedora 10 

. /var/www/lighttpd/shellscript/config.sh

CONF_FNAME="guestos.conf"
CONF_FPATH="/var/$CONF_FNAME"
MPDIR="/mnt"
VERSION="1.3"
${DEBUG:=false}

debug(){
	test $DEBUG && echo "*********" $*
}
_confsave(){
	declare MP=$1
	mkdir -p `dirname ${MP}${CONF_FPATH}`
	if [ -f "${MP}${CONF_FPATH}" ];then
		rm -f "${MP}${CONF_FPATH}.bak"
		mv "${MP}${CONF_FPATH}" "${MP}${CONF_FPATH}.bak"
	fi
	cp -f "${CONF_FPATH}" "${MP}${CONF_FPATH}" && return 0 || return 1
}
_confmountandsave(){
	declare PART=$1
	declare MP=$MPDIR/$PART
	mkdir -p $MP
	mount /dev/$PART $MP 2>/dev/null
	if [ "$?" = "0" ]; then
		_confsave $MP 
		if [ "$?" = "0" ]; then
			echo $PART > $CONF_FPATH.part
			echo $PART
			umount $MP
			debug "try to save to $PART success"
			return 0
		else
			umount $MP
			debug "try to save to $PART fail"
			return 1
		fi
	else
		debug "try to mount $PART fail"
		return 1
	fi
}
_confwhateversave(){
	declare PART=$1
	debug "try to saving to $PART"
	df -T 2>/dev/null | grep "^/dev/$PART "
	if [ "$?" = "0" ]; then 
	# if the partition had been mounted, just save it
		declare MP=`df -T 2> /dev/null | grep "^/dev/$PART " | awk '{print $7}'`
		_confsave $MP
		if [ $? = 0 ]; then
			debug "try to save to $PART success"
			echo $PART > $CONF_FPATH.part
			echo $PART
			return 0
		else
			debug "try to save to $PART fail"
			return 1
		fi
	else
	# try to mount it and save
		_confmountandsave $PART && return 0 || return 1
	fi
}

saveconfig()
{
	# usage: saveconfig [partition_id]
	# if partition_id not specify, first try to get the configure from $CONF_FPATH;
	#	then try to mount the partion one by one and print partition_id
	NCOPY=0
	if [ -n "$1" ]; then		
	
		if [ -f "${CONF_FPATH}.part" ]; then
			declare PART=`cat ${CONF_FPATH}.part`
			# if the partition had been mounted
			_confwhateversave $PART && return 0 || return 1
		else
			# if not specify what partition, then try to mount one by one
			#declare ALLDISKS=`fdisk -l 2>/dev/null | grep /dev | grep Disk | awk '{print $2}' | cut -c 6- | tr -d :`
			declare ALLDISKS=`fdisk -l 2>/dev/null| grep ":" | grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1`
			for DISK in $ALLDISKS; do
				for PART in `fdisk -l /dev/$DISK 2>/dev/null| grep ^/dev | tr -d \* |awk '{print $1}'| cut -c 6-`; do
					if $DEBUG; then
						_confwhateversave $PART
						if [ $? = 0 ]; then
							((NCOPY=$NCOPY+1))
						else
							echo "Could not save to $PART" >&2
							continue
						fi
					else
						_confwhateversave $PART 2>/dev/null
						if [ $? = 0 ]; then
							((NCOPY=$NCOPY+1))
						else
							echo "Could not save to $PART" >&2
							continue
						fi
					fi
				done
			done
			# fail at last
			if [ $NCOPY -lt 2 ]; then
				echo "Save configuration fail" >&2
				return 1
			else
				return 0
			fi
			
		fi
	else
		declare PART=$1
		_confwhateversave $PART && return 0 || return 1
	fi
}

#will mount ntfs part,insmod fuse.ko first
ntfs_saveconfig()
{
    insmod /lib/modules/3.1.0-7.fc16.x86_64/kernel/fs/fuse/fuse.ko
    ntfs-3g "/dev/"$1 /mnt
    mkdir -p /mnt/var/

    cp -rf $CONF_FPATH /mnt/var/
    umount /mnt	

    return 0
}

usage()
{
  echo "usage: $1 [-h] [PARTITION_ID]"
  echo " version $VERSION: save the configure file to the disk"
  echo "	-h print this message and exist"
  echo ""
  echo "	if specify the PARTITION_ID, then save the configure file from $CONF_FPATH to the disk."
  echo "	if PARTITION_ID didn't specify, first try to get the PARTITION_ID from $CONF_FPATH.part"
  echo "		or try to mount the partition one by one, and save to the partition"
  echo ""
  echo "	print the partition_id that had save the configure file"
  echo ""
  echo "	the supported filesystem had been registed in /etc/filesystem: "
  echo "	version 1.2: support vfat;minix;xfs;ext2;ntfs;ext3;ntfs-3g;jfs;reiserfs;"
  exit 1
}

if [ "$1" = "-h" ]; then
	usage $0
else
    if [ -f $CONF_FPATH ]; then
            #if `fdisk -l|grep '/dev/[a-z]\{1,2\}d.2'|grep NTFS`	
	    #if echo `fdisk -l|grep '/dev/'$1|grep NTFS >/dev/null` ;then
		#ntfs_saveconfig $1 && exit 0 || exit 1
            #fi

        saveconfig $1 && exit 0 || exit 1

    else
	debug "configure file not exist"
    fi
fi
