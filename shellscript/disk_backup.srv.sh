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
  #return 0
  declare TMPFILE=/tmp/`uuidgen`
  declare IMGSIZE=`$FTPCMD -e "$FTPOPT; ls $FTPPATH; quit;" | grep $IMGNAME$ | awk '{print $5}'`
  declare IMGSIZE=`echo "$IMGSIZE/1000" | bc`
  touch $TMPFILE
  tasklog "Start checking md5" 
  
  echo "Checking md5" > $MESSAGEFILE
  #wget -q --tries=3 --wait=180 --timeout=60 $FTPURL/$FTPPATH/$IMGNAME -O - | $jetcat -f 1000 -p $IMGSIZE 2> $PROGRESSFILE | md5sum | awk '{print $1}' > $TMPFILE

  if [ "$TEMPLATEBASED" == "" ];  then
     wget -q --tries=3 --wait=180 --timeout=60 $FTPURL/$FTPPATH/$IMGNAME -O - | $jetcat -f 1000 -p $IMGSIZE 2> $PROGRESSFILE | md5sum | awk '{print $1}' > $TMPFILE
  else
     wget -q --tries=3 --wait=180 --timeout=60 $FTPURL/$FTPPATH/$TPLNAME/patch -O - | $jetcat -f 1000 -p $IMGSIZE 2> $PROGRESSFILE | md5sum | awk '{print $1}' > $TMPFILE
  fi

  if [ $? -ne 0 ]
   then
     rm -f $TMPFILE
     return 1
  fi  
  
  declare smd5=`head -1 $MD5FILE`
  test "$TEMPLATEBASED" == "" && smd5=`head -1 $MD5FILE` || smd5=`head -1 $MD5PATCHFILE`
  declare tmd5=`head -1 $TMPFILE`
  tasklog "Local md5($smd5) VS Remote md5 ($tmd5) " 
  if [ "$smd5" != "$tmd5" ];  then
     echo "Local md5($smd5) VS Remote md5 ($tmd5) Error"
     rm -f $TMPFILE
     return 1
  else
     echo "Local md5($smd5) VS Remote md5 ($tmd5) OK"
     rm -f $TMPFILE
     #echo -n $smd5 > /var/$TPLNAME.md5
     echo -n $smd5 > /var/$TASKID.md5
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
     echo -n $DISKSIZE > /var/$TASKID.size
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

clearpatchandfinish()
{
   #$FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME"_"$TPLNAME.patch;quit;"
   finishtask $1 $2
}

dd_backup()
{
   createpipe   $TRANPIPE
   createpipe   $MD5PIPE
   createpipe   $MD5TEMPLATEPIPE

   declare TMPFILE=/tmp/`uuidgen`
   
   declare diskname=`basename  $SOURCEDISK`
   declare disksize=`getdevicesize $diskname`
   
   ((DISKSIZE=disksize/1024));
   ((HASHSIZE=((disksize/(1024*1024))*60)/1024))
   
   ((TOTALSIZE=DISKSIZE+HASHSIZE))
   
   $FTPCMD       -e "$FTPOPT; cd $FTPTPLPATH; mkdir $TPLNAME;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; rm $IMGNAME;quit;"   
   
   if [ $MD5LOGORNOT == "YES" ];then
       #tony add, add upload template log for making patch
       #upload disk md5 log
       echo "dcfldd  if=$SOURCEDISK cloudmode=init | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE > $MD5TEMPLATEPIPE"
       dcfldd  if=$SOURCEDISK cloudmode=init | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE > $MD5TEMPLATEPIPE &
       
       tasklog 		"Start upload template md5 log"  
       echo 		"Upload template md5 log:" > $MESSAGEFILE 
       echo "$FTPCMD -e $FTPOPTL; cd $FTPPATH; put $MD5TEMPLATEPIPE -o $IMGNAME.templatemd5; quit;"
       $FTPCMD    -e "$FTPOPTL; cd $FTPPATH; put $MD5TEMPLATEPIPE -o $IMGNAME.templatemd5; quit;"  2>$TMPFILE    
    
       if [ $? -ne 0 ]; then
         tasklog "Upload template md5 fail:`cat $TMPFILE`"
         rm -f $TMPFILE
         deletepipe   $MD5TEMPLATEPIPE
       elif [ $? -eq 0 ]; then
         tasklog "Upload template md5 success!"
       fi
   fi    

   md5sum       $MD5PIPE | awk {'print $1'}> $MD5FILE&
   dd           if=$SOURCEDISK bs=1M | $jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | gzip | tee $MD5PIPE > $TRANPIPE &
   


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

   echo "partition,block,full" > "$IMGNAME.type"

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

#tony add, make patch
dd_makepatch()
{
   createpipe $PATCHPIPE
   createpipe $MD5PATCHPIPE  
   
   declare TMPFILE=/tmp/`uuidgen`
   #declare TMPFILE=/tmp/$1
   
   declare diskname=`basename  $SOURCEDISK`
   declare disksize=`getdevicesize $diskname`
   
   ((DISKSIZE=disksize/1024));   
   ((HASHSIZE=((disksize/(1024*1024))*60)/1024))
   
   #first thing is download the template's size, if newer is bigger 15% than old template, stop it
   echo 		"Download template's size" > $MESSAGEFILE
   echo "wget $WGETOPT $IMGSIZEURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATESIZE"
   wget $WGETOPT $IMGSIZEURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATESIZE  
   
   declare templatesize=`cat $TEMPLATESIZE` 
   if [ $templatesize -le $disksize ];then
     ((bigger=$disksize - $templatesize))
     ((validbigger=15*$templatesize/100))
     if [ $bigger -gt $validbigger ];then
       echo "templatesize:"$templatesize
       echo "disksize:"$disksize
       echo "bigger:"$bigger
       echo "validbigger:"$validbigger
       return 10
     fi
   else
       echo "templatesize:"$templatesize
       echo "disksize:"$disksize   
       return 10
   fi
   
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH; mkdir $TPLNAME;quit;"   
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; rm patch;quit;"   
         
   #second thing is download the template's md5 file
   echo 		"Download template's md5 log:" > $MESSAGEFILE
   echo "wget $WGETOPT $IMGURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATEHASHLOG"
   wget $WGETOPT $IMGURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATEHASHLOG
   #wget $WGETOPT $IMGURL -O $DIFFEHASHLOG | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATEHASHLOG
   
   if [ $? -ne 0 ];then
     tasklog "download template md5 file fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $PATCHPIPE
     deletepipe   $MD5PATCHPIPE
     return 2
   elif [ $? -eq 0 ];then
     tasklog "download template md5 log success!"
   fi
   
   #caculate the local image md5 log for compare with the template md5 log
   echo 		"Generate template's md5" > $MESSAGEFILE
   echo "if=$SOURCEDISK cloudmode=init | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$APPTEMPLATEHASHLOG"
   dcfldd if=$SOURCEDISK cloudmode=init | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$APPTEMPLATEHASHLOG

   echo "if=$TEMPLATEHASHLOG ifdes=$APPTEMPLATEHASHLOG of=$DIFFEHASHLOG cloudmode=difflog"
   dcfldd if=$TEMPLATEHASHLOG ifdes=$APPTEMPLATEHASHLOG of=$DIFFEHASHLOG cloudmode=difflog
   
   #check  
   echo 		"Generate patch:" > $MESSAGEFILE  
   echo "dcfldd  if=$SOURCEDISK mask=$DIFFEHASHLOG cloudmode=directCreatePatch | $jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | gzip > $MD5PATCHPIPE "
   #here
   md5sum       $MD5PATCHPIPE | awk {'print $1'}> $MD5PATCHFILE &
   dcfldd  if=$SOURCEDISK mask=$DIFFEHASHLOG cloudmode=directCreatePatch | $jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | gzip | tee $MD5PATCHPIPE >$PATCHPIPE &
   
   tasklog 		"Start upload patch data..."   
   echo "$FTPOPTL; cd $FTPPATH/$TPLNAME; put $PATCHPIPE -o patch; quit;"
   
   #here we need to consider where the patch will put
   echo 		"Start upload patch data:" > $MESSAGEFILE
   $FTPCMD -e "$FTPOPTL; cd $FTPPATH/$TPLNAME; put $PATCHPIPE -o patch; quit;"  2>$TMPFILE
   
   if [ $? -ne 0 ];then
     tasklog "Upload patch fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $PATCHPIPE
     deletepipe   $MD5PATCHPIPE
     return 1
   elif [ $? -eq 0 ];then
     echo 		"Upload patch data ok" > $MESSAGEFILE
     tasklog "Upload patch success!"
   fi
   
   echo "$FTPOPT; cd $FTPPATH/$TPLNAME; rm patch.size;quit;+++$FTPOPT; cd $FTPPATH/$TPLNAME; put $TMPFILE -o patch.size; quit;"
   # upload disk size
   echo `getdevicesize $diskname` > $TMPFILE
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; rm patch.size;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; put $TMPFILE -o patch.size; quit;"
   
   if [ $? -ne 0 ];then
     tasklog "Upload disk size fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $PATCHPIPE
     deletepipe   $MD5PATCHPIPE
     return 1
   fi    
   # Upload patch md5
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; rm patch.md5;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; put $MD5PATCHFILE -o patch.md5; quit;" 2> $TMPFILE   
   
   if [ $? -ne 0 ];then
     tasklog "Upload patch md5 fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     deletepipe   $TRANPIPE
     deletepipe   $MD5PATCHPIPE
     return 1
   fi 
   
   echo "partition,block,patch" > "$IMGNAME.type"

   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; rm patch.type;quit;"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; put $IMGNAME.type -o patch.type; quit;" 2> $TMPFILE
   
   if [ $? -ne 0 ];then
     tasklog "Upload type fail:`cat $TMPFILE`"
     rm -f $TMPFILE
     return 1
   fi   
   
   rm -f $TMPFILE
   #rm -f $TEMPLATEHASHLOG
   deletepipe   $PATCHPIPE
   deletepipe   $MD5PATCHPIPE
   return 0   
}


move_name()
{
    echo "move_name"
    echo $IMGNAME 	#rm $IMGNAME.size; 
    declare smd5=`head -1 $MD5FILE`
    #$FTPCMD  -e "$FTPOPT; mv $FTPTPLPATH/$TPLNAME $FTPTPLPATH/$smd5; cd $FTPTPLPATH/$smd5; rm $IMGNAME.md5; rm $IMGNAME.size; rm  $IMGNAME.type; rm $IMGNAME.templatemd5; quit;"
    $FTPCMD  -e "$FTPOPT; mv $FTPTPLPATH/$TPLNAME $FTPTPLPATH/$smd5; cd $FTPTPLPATH/$smd5; rm $IMGNAME.md5; rm  $IMGNAME.type; quit;"

    return 0
}

move_name_patch()
{
    echo "move_patch_name"
    echo $IMGNAME 	#rm $IMGNAME.size; 
    declare smd5=`head -1 $MD5PATCHFILE`
    $FTPCMD  -e "$FTPOPT; mv $FTPTPLPATH/$TEMPLATEPATH/$TPLNAME $FTPTPLPATH/$TEMPLATEPATH/$smd5; quit;"

    return 0
}


disk_cleanup()
{
    echo "*********Disk Cleanup Start,Please wait ************"
    PART=$1
    mount $PART /mnt
    dd if=/dev/zero of=/mnt/zero.txt
    rm -rf /mnt/zero.txt
    umount /mnt
    echo "*********Disk Cleanup End **************************"

    return 0
}


FTPPASSWD=""
FTPUSER=""

main()
{
  echo "**************main start()*****************"
  echo $*
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
  export SIXTHPARAM=$6
  export TEMPLATEBASED=$7
 
  echo "param:"$#
 
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
  export FTPOPT="set  dns:fatal-timeout 60;set dns:max-retries 3; set net:timeout 60;set  net:max-retries 3;  set net:reconnect-interval-multiplier 1;set  net:limit-rate 2048000;"
  export FTPOPTL="set  dns:fatal-timeout 60;set dns:max-retries 3;"  
 
  inittask $TASKID

  tasklog "input is $*"  
  check_ftp "$FTPCMD" &&  tasklog "Checking ftp server pass" || finishtask "RESULT_FAIL" "Connect to ftp server failed"
  
  #tony modify, add condition to judge patch or backup
  if [ "$TEMPLATEBASED" == "" ] ; then 
    export FTPPATH=$FTPPATH/$TPLNAME
    export MD5LOGORNOT=$SIXTHPARAM

    #disk_cleanup $SOURCEDISK  && tasklog "Disk Cleanup pass"
    check_disksize && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Disk too big"    
    dd_backup 	&& tasklog "Upload image done" || clearandfinish "RESULT_FAIL" "Create image failed"    
    #backup_checkmd5 && finishtask 0 "Create image Done" || clearandfinish 1 "Check MD5 failed. It's better to recreate the image again" 
    backup_checkmd5 &&  tasklog "Create image Done" || clearandfinish 1 "Check MD5 failed. It's better to recreate the image again" 
    move_name && finishtask "RESULT_SUCCESS"  "Move template name Done"
  else 
    export TEMPLATEPATH=$TEMPLATEBASED
    export WGETOPT="--tries=3 --wait=180 --connect-timeout=60 --timeout=60 -q"     
    export IMGURL=$FTPURL/$FTPTPLPATH/$TEMPLATEPATH/$IMGNAME.templatemd5
    export IMGSIZEURL=$FTPURL/$FTPTPLPATH/$TEMPLATEPATH/$IMGNAME.size
    export FTPPATH=$FTPPATH/$TEMPLATEPATH
   
    #the final goal is to put patch to the ftp server
    check_disksize && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Disk too big" 
    dd_makepatch && tasklog "Upload Patch done" || clearpatchandfinish 1 "RESULT_FAIL" "Create Patch failed" 
    backup_checkmd5 &&  tasklog "Create Patch Done" #|| clearandfinish 1 "Check MD5 failed. It's better to recreate the image again" 
    move_name_patch && finishtask "RESULT_SUCCESS"  "Move template name Done"
	
    #move the template uuid to md5,and rm *.md5,*.size
  fi
 
}


main $*
