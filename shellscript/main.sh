#!/bin/bash

# mmhuang001@gmail.com

# version 0.1 2009-12-15
# features:
# *backup and restall file and device to ftp server.
# *have md5 checking.
# *no local tempfile

FTPSER=192.168.1.2
FTPUSER=centos
FTPPASSWD=centos
FTPPATH=imagestore
FTPCMD="lftp $FTPUSER:$FTPPASSWD@$FTPSER"
FTPURL="ftp://$FTPUSER:$FTPPASSWD@$FTPSER"

#target device and source device for backup, you can overvide it to file name, for test.
TARGETDEV=/tmp/test.img
SOURCEDEV=/dev/hda1

IMGNAME=boot.img
IMGID="013cd3f6-de5a-4582-8b33-1e1cf1ccfcbf"
FTPIMGPATH=/$IMGID
BACKUPPIPE=backup.pipe

MD5FILE=/tmp/$IMGNAME.md5
MD5PIPE=md5.pipe

OPTION_USELOCALCACHE=NO
OPTION_ENCRYPT=AES3
BACKUPTYPE=
FLOWCMD=


usage()
{
   
}

createpipe()
{
  mkfifo $1
}

deletepipe()
{
  rm -f $1
}

dd_backup()
{
   createpipe   $TRANPIPE
   createpipe   $MD5PIPE

   md5sum       $MD5PIPE > $MD5FILE&
   dd           if=$SOURCEDEV bs=1M | gzip | tee $MD5PIPE > $TRANPIPE &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $TRANPIPE -o $FTPIMGPATH/$IMGNAME; quit;" &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME.md5;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $MD5FILE -o $FTPIMGPATH/$IMGNAME.md5; quit;"

   deletepipe   $TRANPIPE
   deletepipe   $MD5PIPE
}


dd_restore()
{
   createpipe   $MD5PIPE

   md5sum       $MD5PIPE > $MD5FILE.bak &
   wget         $FTPURL/$FTPIMGPATH/$IMGNAME -O - | tee $MD5PIPE | gunzip -c | dd of=$TARGETDEV bs=1M

   deletepipe   $MD5PIPE
}

# arg1 = mountpoint
ext3_fullbackup()
{
   createpipe   $TRANPIPE
   createpipe   $MD5PIPE
   MOUNTPOINT=$1

   md5sum       $MD5PIPE > $MD5FILE&
   dump         -z5 -u0f - $MOUNTPOINT| tee $MD5PIPE > $TRANPIPE &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $TRANPIPE -o  $FTPIMGPATH/$IMGNAME; quit;" &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME.md5;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $MD5FILE -o $FTPIMGPATH/$IMGNAME.md5; quit;"

   deletepipe   $TRANPIPE
   deletepipe   $MD5PIPE
   
}

# arg1 = mountpoint

ext3_fullrestore()
{ 
   createpipe   $MD5PIPE
   MOUNTPOINT=$1
   cd $MOUNTPOINT  
   md5sum       $MD5PIPE > $MD5FILE.bak &
   wget         $FTPURL/$FTPIMGPATH/$IMGNAME -O - | tee $MD5PIPE | restore -y -f - 

   deletepipe   $MD5PIPE

}

ntfs_fullbackup()
{
   createpipe   $TRANPIPE
   createpipe   $MD5PIPE
   MOUNTPOINT=$1

   md5sum       $MD5PIPE > $MD5FILE&
   ntfsclone --save-image --output - $SOURCEDEV | gzip -c | tee $MD5PIPE > $TRANPIPE &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $TRANPIPE -o  $FTPIMGPATH/$IMGNAME; quit;" &

   $FTPCMD       -e "cd $FTPPATH; rm $IMGNAME.md5;quit;"
   $FTPCMD       -e "cd $FTPPATH; put $MD5FILE -o $FTPIMGPATH/$IMGNAME.md5; quit;"

   deletepipe   $TRANPIPE
   deletepipe   $MD5PIPE

}

ntfs_fullrestore()
{
   createpipe   $MD5PIPE
   MOUNTPOINT=$1
   cd $MOUNTPOINT
   md5sum       $MD5PIPE > $MD5FILE.bak &
   wget         $FTPURL/$FTPIMGPATH/$IMGNAME -O - | tee $MD5PIPE | ntfsclone --restore-image --overwrite $TARGETDEV -

   deletepipe   $MD5PIPE
}

mbr_backup()
{
  
}
mbr_restore()
{

}


# test
dd_backup
dd_restore
diff $MD5FILE $MD5FILE.bak
