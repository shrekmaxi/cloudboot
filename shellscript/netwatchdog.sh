#!/bin/bash

CONTINUEWATCH=0
# check progress no progress last for long time, just terminate the task
# this script should be call before the main process start
netwatchdog()
{
    # get trigger
	# $1 was the main process id
	# $2 was the identify key

	# this script should be call before the main process start
    # sleep	a second to let the main process start
	sleep 5
	
	declare SCRPID=$1
	declare MYPID=$$
	declare TMPFILE=/tmp/`uuidgen`
	declare NETPID=`ps -ef | grep $SCRPID |grep -v $$ | grep "$2"  | awk '{print $2}'`
    echo "netpid = [$NETPID]" 1>&2
	echo "watching process is $NETPID:`ps -ef | grep $NETPID`" >> /tmp/watchlist
	declare DELAYACTION=0
	
	while true
	  do
		# if the socket does not exist the proccess should be terminated.
		netstat -pautnv 2>&1 | grep $NETPID
		# if socket doesn't exist
		if [ $? -ne 0 ]; then
			sleep 5
			
			# if socket doesn't exist but process exist
			ps -ef | grep $NETPID | grep -v "grep"
			if [ $? -ne 0 ]; then
				# if socket doesn't exist and process doesn't exist
			    echo "healthy: socket miss,and process ended"
				break
			else
			    echo "problem: socket miss,but process exist"
				if [ $DELAYACTION -ne 0 ]; then
				    # kill subprocess and main process
					echo "try to kill $NETPID" 1>&2
					kill -9 $NETPID
					break
				else
					((DELAYACTION++))
				fi
			fi
		else
			echo "progress running."
		fi
		sleep 8
      done
}
netwatchdog $*