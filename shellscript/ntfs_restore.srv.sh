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
   echo -e "\t$0 -h -t retry taskid imageurl targetdisk imagedisksize md5"
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

        tasklog "Start download image"
        echo "Download image:" > $MESSAGEFILE

		bash /var/www/lighttpd/shellscript/netwatchdog.sh $$ "$TMPFILE" >/dev/null &
        ((DISKSIZE=$IMGDISKSIZE/1024))
        echo "$WGETOPT $IMGURL -O - -a $TMPFILE | tee $MD5PIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | ntfsclone --restore-image --overwrite $TARGETDEV -"
        wget $WGETOPT $IMGURL -O - -a $TMPFILE | tee $MD5PIPE | gunzip -c |$jetcat -f 1000 -p $DISKSIZE 2>$PROGRESSFILE | ntfsclone --restore-image --overwrite $TARGETDEV -

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

   if [ "$LOCALMD5" = "$IMGMD5" ]
     then
                return 0
     else
                tasklog "local image md5($LOCALMD5) VS source image md5 ($IMGMD5)"
                return 1
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

        export TASKID=$1
        export IMGURL=$2
        export TARGETDEV=$3
        export IMGDISKSIZE=$4
        export IMGMD5=$5

        export WGETOPT="--tries=3 --wait=180 --connect-timeout=60 --timeout=60 -q" 
        echo "TARGETDEV=$TARGETDEV;IMGURL=$IMGURL;IMGDISKSIZE=$IMGDISKSIZE;IMGMD5=$IMGMD5"
        inittask $TASKID

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
                        break
                else
                        if [ $i -lt $RETRY ]; then
                                tasklog "Checking image md5 fail, Retry $i"
                        else
                                finishtask 1 "Install image md5 fail, Please try again or the VM may crashed"
                        fi
                fi
        done
        finishtask 0 "Install image done"

        #hookconf $ARGCONF && finishtask "RESULT_SUCCESS" "Install image done"

}

main $*


