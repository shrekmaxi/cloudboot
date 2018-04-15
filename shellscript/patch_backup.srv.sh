#!/bin/bash

# mmhuang001@gmail.com

# version 0.1 2009-12-15
# features:
# *backup and restall file and device to ftp server.
# *have md5 checking.
# *no local tempfile


# includ configuration first

jetcat=jetcat-mod

. /var/www/lighttpd/shellscript/config.sh
. /var/www/lighttpd/shellscript/include.sh


usage()
{
   echo "Usage:"
   echo -e "\t$0 -h -u ftpuser -p ftppassword ftpserverip tplname sourcedisk imgname"
   echo -e "\t  -h: print this message"
   echo -e "\t  -u: ftp user name"
   echo -e "\t  -p: ftp password"
   exit 1
}

debug()
{
   echo $1
}

backup_checkmd5()
{
  echo "pass check md5"
  return 0
  declare TMPFILE=/tmp/`uuidgen`
  declare IMGSIZE=`$FTPCMD -e "$FTPOPT; ls $FTPPATH; quit;" | grep $IMGNAME$ | awk '{print $5}'`
  declare IMGSIZE=`echo "$IMGSIZE/1000" | bc`
  touch $TMPFILE
  tasklog "Start checking md5"
  echo "Checking md5" > $MESSAGEFILE
  wget -q --tries=10 --wait=120 --timeout=12 -q $FTPURL/$FTPPATH/$IMGNAME -O - | $jetcat -f 1000 -p $IMGSIZE 2> $PROGRESSFILE | md5sum | awk '{print $1}' > $TMPFILE

  if [ $? -ne 0 ]
   then
    rm -f $TMPFILE
    return 1
  fi  

  declare smd5=`head -1 $MD5FILE`
  declare tmd5=`head -1 $TMPFILE`
  tasklog "Local md5($smd5) VS Remote md5 ($tmd5) " 
  if [ "$smd5" != "$tmd5" ];  then
     rm -f $TMPFILE
     return 1
  else
     rm -f $TMPFILE
     return 0  
  fi

} 

getdevicesize(){
	device_id=$1
	declare devsize=`cat /proc/partitions | grep $device_id$ | awk '{print $3}'`
	echo "$devsize * 1024" | bc
	return 0
}


check_disksize()
{
    
   declare diskname=`basename  $SOURCEDISK`
   ((DISKSIZE=`getdevicesize $diskname`));
 
   if [ $DISKSIZE -le $DISKMAXSIZE ];then
     return 0
   else
     return 1
   fi

}

clearandfinish()
{
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME.size;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME.md5;quit;"
   finishtask $1 $2
}

dd_backup()
{
   createpipe   $TRANPIPE
   createpipe   $MD5PIPE

   declare TMPFILE=/tmp/`uuidgen`
   
   declare diskname=`basename  $SOURCEDISK`
   declare disksize=`getdevicesize $diskname`
   
   ((DISKSIZE=disksize/1024));

   md5sum       $MD5PIPE | awk {'print $1'}> $MD5FILE&
   dd           if=$SOURCEDISK bs=1M | $jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | gzip | tee $MD5PIPE > $TRANPIPE &
   
   $FTPCMD       -e "$FTPOPT; cd $FTPTPLPATH; mkdir $TPLNAME;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME;quit;"

   tasklog 		"Start upload image"
   echo 		"Upload image:" > $MESSAGEFILE
   bash /var/www/lighttpd/shellscript/netwatchdog.sh $$ "put $TRANPIPE" >/dev/null &
   $FTPCMD       -e "$FTPOPTL; cd $FTPPATH; put $TRANPIPE -o $IMGNAME; quit;"  2>$TMPFILE
   
   if [ $? -ne 0 ]; then
     tasklog "Upload image fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $TRANPIPE
     deletepipe   $MD5PIPE
     return 1
   fi
   echo "" > $MESSAGEFILE
   
   # upload disk size
   echo `getdevicesize $diskname` > $TMPFILE
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME.size;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; put $TMPFILE -o $IMGNAME.size; quit;" 
   
   rm -f $TMPFILE

   # Upload md5
 
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME.md5;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; put $MD5FILE -o $IMGNAME.md5; quit;" 2> $TMPFILE
   
   if [ $? -ne 0 ];then
     tasklog "Upload md5 fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $TRANPIPE
     deletepipe   $MD5PIPE
     return 1
   fi

   echo "blockfull" > "$IMGNAME.type"

   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME.type;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; put $IMGNAME.type -o $IMGNAME.type; quit;" 2> $TMPFILE
   
   if [ $? -ne 0 ];then
     tasklog "Upload type fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     return 1
   fi
   
   rm -f $TMPFILE
   deletepipe   $TRANPIPE
   deletepipe   $MD5PIPE
   return 0
}

FTPPASSWD=""
FTPUSER=""

main()
{
 #FTPPATH: the folder where the image would be stored 
 export FTPPATH=$FTPTPLPATH

 if [ $# -lt 4 ]
  then
    usage
  else
   while getopts u:p:h OPTION
   do
    case $OPTION
    in
     p)FTPPASSWD=$OPTARG;;
     u)FTPUSER=$OPTARG;;
     h)usage;;
     \?)echo "Invalid!$OPTION";;
    esac
   done
 fi
 
 if [ $OPTIND -gt $# ]
  then
   usage
 fi
 
 shift `expr $OPTIND - 1`

 if [ $# -lt 3 ]
   then
    usage
 fi

 export TASKID=$1
 export FTPSER=$2
 export TPLNAME=$3
 export SOURCEDISK=/dev/$4
 export IMGNAME=$5
 export FTPPATH=$FTPPATH/$TPLNAME
 

 if [ -n "$FTPPASSWD" -a -n "$FTPUSER" ] ; then
        export FTPCMD="lftp $FTPUSER:$FTPPASSWD@$FTPSER"
        export FTPURL="ftp://$FTPUSER:$FTPPASSWD@$FTPSER"
 elif [  -n "$FTPUSER" ];then
        export FTPCMD="lftp $FTPUSER@$FTPSER"
        export FTPURL="ftp://$FTPUSER@$FTPSER"
 else
        export FTPCMD="lftp $FTPSER"
        export FTPURL="ftp://$FTPSER"
 fi

  echo "TASKID=$TASKID;FTPSER=$FTPSER;TPLNAME=$TPLNAME;SOURCEDISK=$SOURCEDISK;IMGNAME=$IMGNAME;FTPPATH=$FTPPATH;FTPCMD=$FTPCMD;FTPURL=$FTPURL;"

# export FTPOPT="set  dns:fatal-timeout 10;set net:timeout 10; set  net:limit-rate 102400000;set net:max-retries 22;set net:reconnect-interval-base 5;set net:reconnect-interval-multiplier 1;"
 export FTPOPT="set  dns:fatal-timeout 10;set dns:max-retries 3; set net:timeout 10;set  net:max-retries 2;  set net:reconnect-interval-multiplier 1;set  net:limit-rate 1024000;"
 export FTPOPTL="set  dns:fatal-timeout 10;set dns:max-retries 3;"
 #export FTPOPT=""
 inittask $TASKID

 tasklog "input is $*"  
 check_ftp "$FTPCMD" &&  tasklog "Checking ftp server pass" || finishtask "RESULT_FAIL" "Connect to ftp server failed"
 
# check_disksize && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Disk too big"

 dd_backup 	&& tasklog "Upload image done" || clearandfinish "RESULT_FAIL" "Create image failed"
 
 backup_checkmd5 && finishtask 0 "Create image Done" || clearandfinish 1 "Check MD5 failed. It's better to recreate the image again"
}


main $*
