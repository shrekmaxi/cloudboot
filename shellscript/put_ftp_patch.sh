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
   echo -e "\t$0 -h -u ftpuser -p ftppassword ftpserverip sourcedisk imgname"
   echo -e "\t  -h: print this message"
   echo -e "\t  -u: ftp user name"
   echo -e "\t  -p: ftp password"
   exit
}


upload_meta()
{
   echo "**************upload meta start()*****************"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; put /var/$TASKID.meta -o meta; quit;" 
   
   rm -f /var/$TASKID.md5
   rm -f /var/$TASKID.size
   rm -f /var/$TASKID.meta
   return 0
}

upload_patch()
{
   sh /var/www/lighttpd/shellscript/make_patch.sh
   echo "**************upload patch start()*****************"
   $FTPCMD       -e "$FTPOPT; cd $FTPPATH/$TPLNAME; put /var/patch.tar.gz -o patch.tar.gz; quit;" 
   return 0
}

FTPPASSWD=""
FTPUSER=""

main()
{
 echo "**************upload other's start()*****************"
 echo $*
 #FTPPATH: the folder where the image would be stored 
 export FTPPATH=$FTPTPLPATH

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

 if [ $# -lt 3 ]
   then
    usage
    exit
 fi

 export TASKID=$1
 export FTPSER=$2
 export TPLNAME=$3
 export SOURCEDISK=/dev/$4
 export IMGNAME=$5
 export SIXTHPARAM=$6

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

 export FTPOPT="set  dns:fatal-timeout 60;set dns:max-retries 3; set net:timeout 60;set  net:max-retries 3;  set net:reconnect-interval-multiplier 1;set  net:limit-rate 2048000;"
 export FTPOPTL="set  dns:fatal-timeout 60;set dns:max-retries 3;"
 
 #upload_meta

 upload_patch
}


main $*
