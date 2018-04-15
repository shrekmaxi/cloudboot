#!/usr/bin/python

# 2010-2-17
# raymondhuang@powerallnetworks.com

'''
This is included by all python scripts. It defined the all the runtime structures and default options. and it would convert to shell configuration  
'''

config={

    # runtime folders

    #'pcinfopath':'/tmp/pcinfo',
    #'diskinfopath':'/tmp/pcinfo',
    'pcinfopath':'/tmp/pcinfo',
    'diskinfopath':'/tmp/pcinfo/diskinfo',
    'taskinfopath':'/tmp/taskinfo',
    'curtaskinfopath':'/tmp/taskinfo/curtask',
    'historytaskpath':'/tmp/taskinfo/history',
    # runtime files
    
    'md5pipe':'/tmp/taskinfo/curtask/md5.pipe',
    'tranpipe':'/tmp/taskinfo/curtask/tran.pipe',
    'statuspipe':'/tmp/taskinfo/status.pipe',
    
    # current task information
    
    'md5file':'/tmp/taskinfo/curtask/md5',
    'progressfile':'/tmp/taskinfo/curtask/progress',
    'resultfile':'/tmp/taskinfo/curtask/result',
    'messagefile':'/tmp/taskinfo/curtask/message',
    'detailfile':'/tmp/taskinfo/curtask/detail',
    'idfile':'/tmp/taskinfo/curtask/id',
    'pidfile':'/tmp/taskinfo/curtask/pid',
    'starttimestampfile':'/tmp/taskinfo/curtask/starttimestamp',
    'stoptimestampfile':'/tmp/taskinfo/curtask/stoptimestamp',
    'statusfile':'/tmp/taskinfo/curtask/status',
    'logfile':'/tmp/taskinfo/curtask/logfile',
    
    # system files structure
    
    'shellscriptpath':'/var/www/lighttpd/shellscript',
    'cgipath':'/var/www/lighttpd',
    'htmlpath':'/var/www/lighttpd/html',
    
    # others
    
    'diskmaxsize':53687091200,
    'userid':'cloudimage',
    'ftptplpath':'cloudimage',
	# binding with shell script: osconfsave.sh
	'guestosconfpath':"/var/guestos.conf",
	
	'rpcbox_url':"",
	"rpcbox_uuid":"",
	"bootbox_url":"",
	"bootbox_uuid":"",
	#"confbox_url":"http://box.goodvm.com:8080/msg/",
    "confbox_url":"",
    #'confbox_uuid':  "11111111-1111-1111-1111-111111111111",
    'confbox_uuid':  "",
	#"updatebox_url":"http://box.goodvm.com:8080/msg/",
    #'updatebox_uuid':"22222222-2222-2222-2222-222222222222"
    "updatebox_url":"",
    'updatebox_uuid':"",
    
    #vm info
    
    #CGI user and password
    "powerall":"powerallcloud",
	
}

   
if __name__ == "__main__":
    import os
    print "convert python configure to shell configure"
    
    shcfg = ""
    for k,v in config.iteritems():
        shcfg += "%s=%s\n" % (k.upper(),str(v))
    
    shcfgfile = config['shellscriptpath']+"/config.sh" 
    os.remove(shcfgfile)
    f = file(shcfgfile, 'w')
    f.write(shcfg)
    f.close()
    


