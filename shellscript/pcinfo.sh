#!/bin/bash

. /var/www/lighttpd/shellscript/config.sh
alldisks=""
allparts=""
allnics=""


part_info()
{
netdevices=`cat /proc/net/dev |grep eth |cut -d: -f 1`

#alldisks=`fdisk -l 2>/dev/null | grep /dev | grep Disk | awk '{print $2}' | cut -c 6- | tr -d :`
alldisks=`fdisk -l 2>/dev/null| grep ":" | grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1`
#allparts=`fdisk -l 2>/dev/null | grep ^/dev | awk '{print $2}' | cut -c 6- | tr -d :`

for disk in $alldisks;
do
  diskmetadir=diskinfo/$disk
  mkdir -p $diskmetadir
  echo $disk > $diskmetadir/name

  # get size
  fdisk -l /dev/$disk | grep Disk | grep /dev | head -1 | awk '{print $5}' > $diskmetadir/size

  # get block
  cat /proc/partitions | grep ${disk}$ | awk '{print $3}' > $diskmetadir/block
  
  # get partition
  
  for part in `fdisk -l /dev/$disk 2>/dev/null| grep ^/dev | tr -d \* |awk '{print $1}'| cut -c 6-`;
   do
      partinfodir=$diskmetadir/partitions/$part
      mkdir -p $partinfodir
      echo $part > $partinfodir/name

      # get size
        fdisk -l /dev/$part 2>/dev/null | grep Disk | grep /dev | awk '{print $5}' > $partinfodir/size
      # get block
        cat /proc/partitions | grep ${part}$ | awk '{print $3}' > $partinfodir/block
      # get filesystem
        fdisk -l /dev/$disk | grep ^/dev/$part | tr -d \* | awk '{print $6$7$8}' > $partinfodir/fs
      # boot partition
        fdisk -l /dev/$disk | grep ^/dev/$part | grep \* >/dev/null && echo "true"  > $partinfodir/boot || echo "false"  > $partinfodir/boot

      # try to mount filesystem to get filesystem info

	# adfs, affs, autofs, cifs, coda, coherent, cramfs, debugfs, devpts, efs, ext, ext2, ext3,  hfs,  hfsplus,  hpfs,  iso9660,
	# jfs,  minix, msdos, ncpfs, nfs, nfs4, ntfs, proc, qnx4, ramfs, reiserfs, romfs, smbfs, sysv, tmpfs, udf, ufs, umsdos, usbfs, vfat,
        # xenix, xfs, xiafs
	
	declare FSTYPE=`cat $partinfodir/fs` 
	mkdir -p mnt/$part

        case $FSTYPE 
         in
          Linux)
	      df -T | grep ^/dev/$part 
	      if [ $? = 0 ]; then 
		echo `df -T | grep ^/dev/$part | awk '{print $2}'`>$partinfodir/fs
	      else
	        for fstype in ext3 xfs reiserfs ext2 ext4
	        do
		    #echo "try $part=$fstype"
	            mount -t $fstype -r /dev/$part mnt/$part 2>/dev/null 
		   if [ $? = 0 ]
		     then
			echo $fstype > $partinfodir/fs
		        break;
		     else
	               echo "unknow">$partinfodir/fs			
		   fi
	        done
	      fi
	   ;;
	  HPFS/NTFS)
	      mount.ntfs /dev/$part /mnt/$part && echo "xfs" > $partinfodir/fs || echo "unknow">$partinfodir/fs
	   ;;
          *)
	      echo "unknow">$partinfodir/fs
	   ;;
       esac

       tmpfstype=`cat $partinfodir/fs`
       echo "$part=$tmpfstype"
       if [ "$tmpfstype" != "unknow" ] 
	then
         df -T -x iso9660 -x tmpfs | grep ^/dev/$part | awk '{print $3}' >$partinfodir/fsallsize
         df -T -x iso9660 -x tmpfs | grep ^/dev/$part | awk '{print $4}' >$partinfodir/fsusedsize
         df -T -x iso9660 -x tmpfs | grep ^/dev/$part | awk '{print $5}' >$partinfodir/fsavailablesize
	 umount mnt/$part 2> /dev/null
       fi

   done
done
}

nic_info()
{
  allnics=`cat /proc/net/dev |grep eth |cut -d: -f 1`
  for nic in $allnics
   do
      nicinfodir=nicinfo/$nic
      mkdir -p $nicinfodir
      echo $nic > $nicinfodir/name
   done
}

cpu_info()
{
   cat /proc/cpuinfo | grep -E "^(model name|processor|vendor_id|cpu MHz|cache size|clflush size|$)" > cpuinfo
}

mem_info()
{
   head -6 /proc/meminfo > meminfo  
}
disk_info()
{
   fdisk -l > diskinf
}

mkdir -p $PCINFOPATH
cd $PCINFOPATH

part_info
nic_info
cpu_info
mem_info
disk_info
