#!/bin/bash

# mmhuang001@gmail.com

# version 1.3 2010-12-15
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
   echo -e "\t$0 -h -t retry taskid imageurl targetdisk imagedisksize md5 patchurl"
   echo -e "\t  -h: print this message, and exist"
   echo -e "\t  -t: when md5 checking fail, how many times would be reinstall"
   exit 1
}
getdevicesize(){
        device_id=$1
        declare devsize=`cat /proc/partitions | grep $device_id$ | awk '{print $3}'`
        echo "$devsize * 1024" | bc
        return 0
}

# this function is to check the target disk size less than source disk size
# usage: check_disksize devicename disksize
check_disksize()
{
        declare DISKNAME=`basename  $1`
        echo $DISKNAME
        declare LOCALDISKSIZE=`getdevicesize $DISKNAME`
        declare SOURCEDISKSIZE=$2

        echo $LOCALDISKSIZE vs $SOURCEDISKSIZE
        if [ $LOCALDISKSIZE -lt $SOURCEDISKSIZE ]; then
                tasklog "Target Disk ($LOCALDISKSIZE) is smaller than the source one($SOURCEDISKSIZE)"
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

  TMPFILE=/tmp/`uuidgen`

  createpipe   $MD5PIPE
  md5sum       $MD5PIPE | awk '{print $1}'> $MD5FILE &
  
   
  declare diskname=`basename  $TARGETDEV`
  declare disksize=`getdevicesize $diskname`
 
  ((DISKSIZE=disksize/1024));
  ((HASHSIZE=((disksize/(1024*1024))*60)/1024))  
  
  export IMGMD5LOGURL=`dirname $IMGURL`/`basename $IMGURL.templatemd5`

  #download template based md5 log first
  echo "Download template's md5 log:" > $MESSAGEFILE
  echo "wget $WGETOPT $IMGMD5LOGURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATEHASHLOG"
  wget $WGETOPT $IMGMD5LOGURL -O - -a $TMPFILE | $jetcat -f 1000 -p $HASHSIZE 2>$PROGRESSFILE >$TEMPLATEHASHLOG	        

  tasklog "Start download image"
  echo "Download image:" > $MESSAGEFILE

  bash /var/www/lighttpd/shellscript/netwatchdog.sh $$ "$TMPFILE" >/dev/null &
  ((DISKSIZE=$IMGDISKSIZE/1024))
  echo "wget $WGETOPT $IMGURL -O - -a $TMPFILE | tee $MD5PIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | dd of=$TARGETDEV bs=1M"
  wget $WGETOPT $IMGURL -O - -a $TMPFILE | tee $MD5PIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | dd of=$TARGETDEV bs=1M

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

#tony add, patch the data to original tempalte
dd_patch()
{
  TMPFILE=/tmp/`uuidgen`
  echo $TMPFILE
  
  createpipe   $MD5PATCHPIPE
  md5sum       $MD5PATCHPIPE | awk '{print $1}'> $MD5PATCHFILE &

  tasklog "Start download patch"
  echo "Download patch:" > $MESSAGEFILE
  
  bash /var/www/lighttpd/shellscript/netwatchdog.sh $$ "$TMPFILE" >/dev/null &
  ((DISKSIZE=$IMGDISKSIZE/1024))
  echo "wget $WGETOPT $PATCHURL -O - -a $TMPFILE | tee $MD5PATCHPIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | dcfldd of=$TARGETDEV mask=$TEMPLATEHASHLOG cloudmode=patchNoCalcMd5"
  wget $WGETOPT $PATCHURL -O - -a $TMPFILE | tee $MD5PATCHPIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | dcfldd of=$TARGETDEV mask=$TEMPLATEHASHLOG cloudmode=patchNoCalcMd5

  if [ $? != 0 ]; then    
    echo "" > $MESSAGEFILE
    deletepipe   $MD5PATCHPIPE
    tasklog "`cat $TMPFILE`"    
    rm -f $TMPFILE
    return 1
  else
    echo "" > $MESSAGEFILE
    deletepipe   $MD5PATCHPIPE
    rm -f $TMPFILE
    return 0
  fi
}

restore_checkmd5()
{
   declare LOCALMD5=`cat $MD5FILE`

   if [ "$LOCALMD5" = "$IMGMD5" ]
     then
                return 0
     else
                tasklog "local image md5($LOCALMD5) VS source image md5 ($IMGMD5)"
                return 1
   fi
}
patch_checkmd5()
{
   declare LOCALPATCHMD5=`cat $MD5PATCHFILE`

   if [ "$LOCALPATCHMD5" = "$PATCHMD5" ]; then
       return 0
   else
       tasklog "local patch md5($LOCALPATCHMD5) VS source patch md5 ($PATCHMD5)"
       return 1
   fi
}

patch_guestos()
{
    tasklog "begin to patch,PATCHFILE: $IMGPATCHURL"

 
    rm -rf $TMPPATCHFOLDER
    mkdir $TMPPATCHFOLDER
    TMPPATCHFILE="$TMPPATCHFOLDER/patch.tar.gz"
	TMPPATCHFILE_TAR="$TMPPATCHFOLDER/patch.tar"

    cd $TMPPATCHFOLDER

    #if need patch
    if [ "x$IMGPATCHURL" = "x" ]; then
        #no patch
        tasklog "no patch file"
        return 0;
    else
        tasklog "get patch file: wget $WGETOPT $IMGPATCHURL -O $TMPPATCHFILE "

        wget $WGETOPT $IMGPATCHURL -O $TMPPATCHFILE
        
		if [ $? = 0 ];then
		    tasklog "get patch file done"
            
        else
		    tasklog "get patch file fail"
            return 1
        fi
       
        gzip -d $TMPPATCHFILE
        tar -xf $TMPPATCHFILE_TAR		

        cd $TMPPATCHFOLDER/patch/
        ./patch.sh ${TARGETDEV:5:3}		
		
        #bash $TMPPATCHFOLDER/patch/patch.sh

        if [ $? = 0 ];then
		    #rm -rf $TMPPATCHFOLDER
			tasklog "patch done"
            return 0
        else
		    #rm -rf $TMPPATCHFOLDER
			tasklog "patch fail"
            return 1
        fi

    fi

}

#hookconf()
#{
#       ARGFILE=$1
#       declare TMPFILE=/tmp/`uuidgen`
#       declare TMPLOGFILE=/tmp/`uuidgen`
#       wget $FTPURL/$FTPPATH/$IMGNAME.sh -O $TMPFILE
#       if [ $? != 0 ]; then
#               bash $TMPFILE $ARGFILE 2>$TMPLOGFILE
#               test $? = 0 && tasklog "configure done" || tasklog "`cat $TMPLOGFILE`"
#       fi
#       rm -f $TMPFILE $TMPLOGFILE $ARGFILE
#}

main()
{
    RETRY=1
    if [ $# -lt 4 ];then
      usage
    else
      while getopts t:h OPTION
      do
        case $OPTION
        in
          h)  usage;;
          t)  export RETRY=`echo $OPTARG+0 | bc`
                  test $RETRY -lt 1 && usage;;
          \?) echo "Invalid!$OPTION";;
        esac
      done
    fi

    if [ $OPTIND -gt $# ];then
      usage
    fi

    shift `expr $OPTIND - 1`
    
    echo "param:"$*
    echo "param num:"$#

    export TASKID=$1
    export IMGURL=$2
    export TARGETDEV=$3
    export IMGDISKSIZE=$4
    export IMGMD5=$5
    
    #tony add, judge install or patch
    if [ -n "$6" ] ; then 
      echo $6 | grep "patch.tar.gz$"
      if [ 0 -ne $? ] ; then
        export PATCHNAME=$6
        export PATCHMD5=$7
        export PATCHSIZE=$8
      else
        export IMGPATCHURL=$6
        export PATCHNAME=$7
        export PATCHMD5=$8
        export PATCHSIZE=$9
      fi
    fi
    
    echo "PATCHSIZE:"$PATCHSIZE
    echo "PATCHMD5:"$PATCHMD5
		
	export TMPPATCHFOLDER="/tmp/ospatch"
    export WGETOPT="--tries=3 --wait=180 --connect-timeout=60 --timeout=60 -q"    
	inittask $TASKID
    tasklog "TARGETDEV=$TARGETDEV;IMGURL=$IMGURL;IMGDISKSIZE=$IMGDISKSIZE;IMGMD5=$IMGMD5;IMGPATCHURL=$IMGPATCHURL"
    
    #tony modify, add condition to decide patch or install
    if [ -n "$PATCHNAME" ] ; then
      echo "begin to make patch,haha..."	    	    	    
      export PATCHURL=$PATCHNAME/patch	  
    	    
    #tony add, check the disk size to decide if have enough size to restore and patch
    check_disksize $TARGETDEV $IMGDISKSIZE && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Target disk is too small"
    check_disksize $TARGETDEV $PATCHSIZE && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Target disk is too small"	    
    	    
    dd_restore
    if [ $? = 0 ];then
    tasklog "Refill image done"
    else
    finishtask 1 "RESULT_FAIL" "Refill image fail, Please try again. or the VM may crashed"
    fi  
    
    # checking md5
    restore_checkmd5
    if [ $? = 0 ];then
    tasklog "Checking image md5 pass"
    else
    finishtask 1 "RESULT_FAIL" "Checking image md5 fail, Please try again or the VM may crashed"
    fi      
    
    dd_patch
    if [ $? = 0 ];then
      tasklog "patch image done"
    else
      finishtask 1 "RESULT_FAIL" "patch image fail, Please try again. or the VM may crashed"
    fi
    
    patch_checkmd5
    if [ $? = 0 ];then
    tasklog "Checking patch md5 pass"
    
      #patch the guest os if need
    patch_guestos
         
    if [ $? = 0 ];then 					   
        tasklog "patch guest os pass"
          break
      else
        finishtask 1 "patch guest os fail, Please try again or the VM may crashed"
      fi        
    else
    finishtask 1 "RESULT_FAIL" "Checking patch md5 fail, Please try again or the VM may crashed"
    fi	     
    
    else    
    check_disksize $TARGETDEV $IMGDISKSIZE && tasklog "Checking Disk size pass" || finishtask "RESULT_FAIL" "Target disk is too small"
    
    for((i=1;i<=$RETRY+1;i++))
    do
      # install image
      dd_restore
      if [ $? = 0 ];then
        tasklog "Refill image done"
      else
        finishtask "RESULT_FAIL" "Refill image fail, Please try again. or the VM may crashed"
      fi
    
      # checking md5
      restore_checkmd5
      if [ $? = 0 ];then
        tasklog "Checking image md5 pass"
              
          #patch the guest os if need
        patch_guestos
             
        if [ $? = 0 ];then 					   
            tasklog "patch guest os pass"
    	      break
          else
            finishtask 1 "patch guest os fail, Please try again or the VM may crashed"
          fi
    
      else
        if [ $i -lt $RETRY ]; then
          tasklog "Checking image md5 fail, Retry $i"
        else
          finishtask 1 "Checking image md5 fail, Please try again or the VM may crashed"
        fi
      fi
    done
    fi
    
    finishtask 0 "Install image done"
    #hookconf $ARGCONF && finishtask "RESULT_SUCCESS" "Install image done"
}

main $*


