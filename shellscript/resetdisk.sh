#!/bin/bash
# mmhuang001@gmail.com version 1.0 2011-1-15 features: *backup and
# restall file and device to ftp server. *have md5 checking. *no local
# tempfile

DISK=/dev/$1
BASEDIR=/var/www/lighttpd/shellscript
#IMGURL="ftp://setup:setup@goodvm.com:21321"

test "x$1" = "x" && exit 1
test -b $DISK || exit 1

#if system disk, need backup kenerl file and ramdisk.gz and config file
if [ "$2" = "sys" ];then
    echo "backup kenerl file and ramdisk.gz and config file"
    MP=/mnt/`basename ${DISK}`1
    mkdir $MP
    mkdir -p /install/
    mount ${DISK}1 $MP

	test $MP/var/cloudrainbow.conf && rm -f /var/cloudrainbow.conf
		
    test -f /install/chaosvm || cp $MP/chaosvm /install/
    test -f /install/ramdisk.gz || cp $MP/ramdisk.gz /install/
	cp $MP/var/cloudrainbow.conf /var/
		
	umount $MP
	rm -rf $MP
fi

echo "set all disk data to 0, it need a long time ,please wait..."
dd if=/dev/zero of=$DISK bs=100M count=10	

#if system disk, need format and install agent again
if [ "$2" = "sys" ];then
    echo "format and install agent"
    bash $BASEDIR/install.sh $1 -f
	
	echo "restore the config file"
    MP=/mnt/`basename ${DISK}`1
    mkdir $MP
    mount ${DISK}1 $MP
	mkdir $MP/var

	cp /var/cloudrainbow.conf $MP/var/
		
	umount $MP
	rm -rf $MP	
	
fi

echo "done"



