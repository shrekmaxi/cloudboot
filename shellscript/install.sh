#!/bin/bash
# mmhuang001@gmail.com version 1.0 2011-1-15 features: *backup and
# restall file and device to ftp server. *have md5 checking. *no local
# tempfile

#install must run from iso or installpack, can not from disk 
test -f /install/chaosvm || exit 0

DISK=/dev/$1
#BASEDIR=/var/www/lighttpd/shellscript
#IMGURL="ftp://setup:setup@goodvm.com:21321"

test "x$1" = "x" && exit 1

if [ $# -lt 2 ] ; then
   echo -n "Careful, install to $DISK might destroy your disk. continue?[y|n]: "

   read -n 1 go
   if [ "$go" != "y" ]; then
	   exit 1
   fi
fi

dd if=/dev/zero of=$DISK bs=1M count=1 
dd if=/dev/zero of=$DISK bs=1M count=10 seek=200

echo "======= step 1 create partition"
fdisk $DISK << EOF
d
1
d
2
d
3
d
4
d
5
d
6
d
7
n
p
1

+200M

n
p
2



w
EOF

parted $DISK set 2 boot on
parted $DISK set 1 hidden on

echo "==========step 2 format"
mkfs.ext3 ${DISK}1

echo "==========step 3 copy files"
MP=/mnt/`basename ${DISK}`1
mkdir $MP
mount ${DISK}1 $MP

cp /install/* $MP
cp -r /grub/ $MP
#touch $MP/chaosvm
#touch $MP/ramdisk.gz
#bash $BASEDIR/update.sh $IMGURL
#cd $MP && tar xvf /grub.tar


echo "==========step 4 setup grub"
echo "(hd0)   ${DISK}" > $MP/grub/device.map
grub <<EOF
    device (hd0) ${DISK}
    root (hd0,0)
    setup (hd0)
    install (hd0,0)/grub/stage1 (hd0) (hd0,0)/grub/stage2 p (hd0,0)/grub/menu.lst    
    quit
EOF

cd /
umount $MP
rm -r $MP
#umount /mnt/cdrom

