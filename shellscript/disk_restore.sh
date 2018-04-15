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
   echo -e "\t$0 -h -u ftpuser -p ftppassword ftpserverip targetdisk imagepath"
   echo -e "\t  -h: print this message"
   echo -e "\t  -u: ftp user name"
   echo -e "\t  -p: ftp password"
   exit
}
getpcinfobyname(){
	device_id=$1
	declare devsize=`cat /proc/partitions | grep $dev_id$ | awk '{print $3}'`
	echo "$devsize * 1024" | bc
	return 0
}


check_disksize()
{
	TMPFILE=/tmp/`uuidgen`
	declare diskname=`basename  $TARGETDEV`
	
    # Get source disk size
	wget $FTPURL/$FTPPATH/$IMGNAME.size -O $TMPFILE;

	if [ $? != 0 ]; then
	    finishtask 1 "Get source disk size error!" 
		rm -f $TMPFILE
	fi
	
	export IMGDISKSIZE=`head -1 $TMPFILE`
	declare DISKSIZE=`getpcinfobyname $diskname size`
	
	rm -f $TMPFILE
	
	if [ $DISKSIZE -lt $IMGDISKSIZE ];then
		tasklog "Target Disk ($DISKSIZE) is smaller than the source one($IMGDISKSIZE)"
		return 1
	else
		return 0
	fi
    

}


# argv:
# 1: imgsize
# 2: targetdevice
# 3: 


dd_restore()
{
	#declare IMGSIZE=`$FTPCMD -e "ls $FTPPATH; quit;" | grep $IMGNAME$ | awk '{print $5}'`
	#declare IMGSIZE=`echo "$IMGSIZE/1000*1.024*1.024*1.024" | bc`
	declare IMGSIZE=`echo "${IMGDISKSIZE}/1024" | bc`
    tasklog "image size is $IMGSIZE"
	
	TMPFILE=/tmp/`uuidgen`
	
	createpipe   $MD5PIPE
	md5sum       $MD5PIPE | awk '{print $1}'> $MD5FILE &
	tasklog "Start download image"
	echo "Download image:" > $MESSAGEFILE
    bash /var/www/lighttpd/shellscript/netwatchdog.sh $$ "a $TMPFILE"&

	wget         $WGETOPT $FTPURL/$FTPPATH/$IMGNAME -O - -a $TMPFILE | tee $MD5PIPE | gunzip -c | $jetcat -f 1000 -p $IMGSIZE 2>$PROGRESSFILE | dd of=$TARGETDEV bs=1M
   
	if [ $? != 0 ]; then
		echo "" > $MESSAGEFILE
 		deletepipe   $MD5PIPE
		rm -f $TMPFILE
		tasklog "`cat $TMPFILE`"
		return 1
	else
		echo "" > $MESSAGEFILE
 		deletepipe   $MD5PIPE
		rm -f $TMPFILE
		return 0
	fi	
}

restore_checkmd5()
{
   declare LOCALMD5=`cat $MD5FILE`
   wget $FTPURL/$FTPPATH/$IMGNAME.md5 -O $MD5FILE.tmp

   declare SRVMD5=`cat $MD5FILE.tmp`
   rm -f $MD5FILE.tmp
   
   if [ "$LOCALMD5" = "$SRVMD5" ]
     then
		return 0
     else
		tasklog "local image md5($LOCALMD5) VS source image md5 ($SRVMD5)"
		return 1
   fi
}

hookconf()
{
	ARGFILE=$1
	declare TMPFILE=/tmp/`uuidgen`
	declare TMPLOGFILE=/tmp/`uuidgen`
	wget $FTPURL/$FTPPATH/$IMGNAME.sh -O $TMPFILE
	if [ $? != 0 ]; then
		bash $TMPFILE $ARGFILE 2>$TMPLOGFILE
		test $? = 0 && tasklog "configure done" || tasklog "`cat $TMPLOGFILE`"		
	fi
	rm -f $TMPFILE $TMPLOGFILE $ARGFILE
}

FTPPASSWD=""
FTPUSER=""


main()
{
 if [ $# -lt 3 ]
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

 export FTPSER=$1
 export TARGETDEV=$2
 export IMGNAME=$3
 export ARGCONF=$4
 export FTPPATH=$FTPTPLPATH

 
 if [ -n $FTPPASSWD -a -n "$FTPUSER" ] ; then
	export FTPCMD="lftp $FTPUSER:$FTPPASSWD@$FTPSER"
	export FTPURL="ftp://$FTPUSER:$FTPPASSWD@$FTPSER"
 elif [  -n "$FTPUSER" ];then
	export FTPCMD="lftp $FTPUSER@$FTPSER"
	export FTPURL="ftp://$FTPUSER@$FTPSER"
 else
	export FTPCMD="lftp $FTPSER"
	export FTPURL="ftp://$FTPSER"
 fi

  export WGETOPT="--tries=10 --wait=120 --timeout=12 -q"
  export FTPOPT="set  dns:fatal-timeout 10;set dns:max-retries 3;set net:timeout 10;set net:max-retries 2;set net:reconnect-interval-base 5;set net:reconnect-interval-multiplier 1;"

	inittask

    check_disksize && tasklog "Checking Disk size pass" || finishtask 1 "Target disk is too small"
	
    check_ftp "$FTPCMD" &&  tasklog "Checking ftp server pass" || finishtask 1 "Connect to ftp server failed"

	dd_restore  && tasklog "Refill image done" || finishtask 1 "Refill image fail, Please try again. or the VM may crashed"

	restore_checkmd5  || finishtask 1 "Checking image md5 fail, Please try again or the VM may crashed"

	hookconf $ARGCONF && finishtask 0 "Install image done"
	
}

main $*

