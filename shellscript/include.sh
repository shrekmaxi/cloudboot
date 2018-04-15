RPCRESULT=
RPCRETURN=
# impletment of RPC SHELL
# argv1:url

SHDEBUG="Y"

shellrpc()
{
   RPCGET=`wget $1 2>/dev/null`
   if [ 0 = $RPCGET ]
   then
   # TODO:test if return 200
   # return format:
   # line 1: result:
   # line 2: return:

    export RPCRESULT `echo $RPCGET | sed -n 1p | cut -c 8- | tr \n \ `;
    export RPCRETURN `echo $RPCGET | sed -e 1d | cut -c 8- `;
    return 0
   else
    export RPCRESULT=""
    export RPCRETURN=""
    return 1
   fi

}

# argv1 object name
# argv2 attribute name

getpcinfobyname()
{
   cat `find $PCINFOPATH/diskinfo -name $2 -type f | grep ${1}/${2}$`
}

createpipe()
{
  mkfifo $1
}

deletepipe()
{
  rm -f $1
}

tasklog()
{
    if [ "$SHDEBUG" = "Y" ]; then
      echo `date +%s` ": $1" 
	fi
	
    echo `date +%s` ": $1" >> $LOGFILE
	  
}

inittask()
{
	if [ -n "$1" ]; then
		export TASKID="$1"
	else
		export TASKID=`uuidgen`
	fi

	mkdir -p 	$HISTORYTASKPATH/$TASKID
	unlink 		$CURTASKINFOPATH
	rm -rf  	$CURTASKINFOPATH
	ln -s 		$HISTORYTASKPATH/$TASKID $CURTASKINFOPATH

	echo $$ 		> $PIDFILE
	echo $TASKID 	> $IDFILE
	echo `date +%s`	> $STARTTIMESTAMPFILE &
	echo "STATUS_BUSY"	> $STATUSFILE &
	echo "0%"		> $PROGRESSFILE
	echo ""			> $MESSAGEFILE
	tasklog "init task" 
	
}

finishtask()
{
	rm -f 	$PIDFILE
	
	echo "STATUS_END" > $STATUSFILE
	test -n "$1" && echo $1 > $RESULTFILE
	test -n "$2" && echo $2 > $MESSAGEFILE
        test -n "$2" && tasklog "$2"
	echo `date +%s`	> $STOPTIMESTAMPFILE &
	#exit $1
	test $1 == "RESULT_SUCCESS" && exit 0 || exit 1
}

check_ftp()
{  
   ftpcmd=$1
   FTPOPT="set  dns:fatal-timeout 60;set dns:max-retries 3; set net:timeout 60;set  net:max-retries 3;  set net:reconnect-interval-multiplier 1;"
   
   $ftpcmd -e "$FTPOPT;ls;quit;" 2>/tmp/checkftp 1> /dev/null
   if [ $? = 0 ]; then
     return 0
   else
     tasklog "`cat /tmp/checkftp`"
     rm -f /tmp/checkftp
     return 1
   fi
}
