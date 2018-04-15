# get pc information and save
'''
This script is to decide to these 4 actions:
1) do configure: [confbox]: default, from cmd, from disk, from net
2) update: [updatebox]:
3) runtask: [rpcbox]: 
4) changeloader : [bootbox]: cgi, shutdown, disk 
'''

from uuid import uuid4
import CloudRainbowAgent
from logging import handlers
import logging
import subprocess
import time
import os
import xmlrpclib
#import threading
import traceback
import lib_json
import CloudRainbowPub 
#import CloudRainbowCGI

distribution="cloudboot"
version=(1,8,"dev")

##Notice: DONOT change this, binding with script file:confget.sh/confsave.sh##
CONF_FNAME="cloudrainbow.conf"
CONF_FPATH="/var/"+CONF_FNAME

def goToGuestOS():
    #when do something success,or error go to guest OS
    print "I will boot to GuestOS"
    #rawExec([os.path.join(config["shellscriptpath"],"bootdisk.sh")])
    #rawExec([os.path.join(config["shellscriptpath"],"boot_guest_os.sh"),getdisktype()],False)
    rawExec([os.path.join(config["shellscriptpath"],"boot_guest_os.sh") +" "+CloudRainbowPub.getdisktype()],False)

def goToCGI():
    print "I will boot to CGI"
    rawExec([os.path.join(config["shellscriptpath"],"bootcgi.sh")],False)
    exit(0)

def auto_install_agent():
    print "I Will Auto Install Agent"
    rawExec([os.path.join(config["shellscriptpath"],"install.sh") + " " + CloudRainbowPub.getdisktype() + " " + "-f"],True)
    print "Install Agent Success"
    goToCGI()
    exit(0)

def repairagent():
    print "Warning I Will Repair Agent,This operation may damage your GuetOS."
    rawExec([os.path.join(config["shellscriptpath"],"repairagent.sh") + " " + CloudRainbowPub.getdisktype() ],True)
    print "Repair Agent Success"
    goToCGI()
    exit(0)
    
def getlocalip():
    #get disk type
    cmd =["ifconfig | grep 'inet addr:' | cut -b 11-"] 
    f = subprocess.Popen(cmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
    f.wait()
    
    return f.stdout.read().strip()

def rawExec(rcmd,wait=True):
    '''
    run command and wait command finished.
    @param rcmd: tuple type value for subprocess modules.
    @return: return {"result":0,"return":"","message":""}
        result: 0 for success, none zero for error.
        message: record the stderr if fail
        return: record the stdout if success
    '''
    ret = {"result":0,"return":"","message":""}
    f = subprocess.Popen(rcmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True,executable='/bin/bash')
    if wait:
        f.wait()
    
    if f.returncode != 0:
        ret["message"] = f.stderr.read()
        ret["result"] = f.returncode
    else:
        ret["message"] = "done"
        ret["result"] = 0
        ret["return"] = f.stdout.read()
        
    return ret;

class TaskDispatcher():
    def __init__(self,config,env):
        '''
        
        @param config:
        @type config:
        '''
        self.conf = config
        self.env = env
        self.syslogger = env["syslogger"]
        self.debug = True
        # run task loop
        self.rpc_list = {}
        self.proxy = xmlrpclib.ServerProxy(self.conf["rpcbox_url"])
        self.currenttask = ""
        self.TaskLoop()
        
    def TaskLoop(self):
        '''
        get task from rpc box and return,
        The rpc_input format should be:
        {
            "timestamp":"",
            "timeout":3600,
            "rpc_methodname":"createImage",
            # Notice: rpc_args should be array
            "rpc_args":[task_info],
            "rpc_callback_url":"",
            "rpc_callback_method":"",
            
        }
        @rtype: {
            "progress":20,
            "message":"",
            "logging":"",
            "result":0
        }

        '''
        while True:
            
            if self.currenttask:
                # update the task status to the rpc box
                method_name = self.currenttask["rpc_input"]["rpc_methodname"]
                if method_name in ["createImage","installImage"]:
                    func = getattr(self.env["module"],"getTaskInfo")
                    ret = func("")
                    if ret["result"] == 0:
                        try:
                            self.proxy = xmlrpclib.ServerProxy(self.conf["rpcbox_url"])
                            self.proxy.RPCUpdateStatus(self.conf["rpcbox_uuid"],self.currenttask["req_uuid"],ret["return"])
                        except Exception,e:
                            if version[2] == "dev":
                                 traceback.print_exc()
                            self.syslogger.error(str(e))
                if self.currenttask["rpc_input"]["timeout"] < time.time() - self.currenttask["rpc_input"]["timestamp"]:
                    #self.proxy.RPCRespond(self.conf["rpcbox_uuid"],self.currenttask["req_uuid"],)
                    raise Exception("Timeout for the rpc task")
            else:
                self.syslogger.info("Get task")
                self.proxy = xmlrpclib.ServerProxy(self.conf["rpcbox_url"])
                ret = self.proxy.getRPCRequestFromQueue(self.conf["rpcbox_uuid"])
                # If no task in queue, it would return error
                if ret["result"] != 0 :
                    raise Exception("Get task error: %s",ret["message"])

                request = ret["return"]
                request["rpc_input"]["timestamp"] = time.time()
                # Parse rpc request
                method_name = request["rpc_input"]["rpc_methodname"]
                param = request["rpc_input"]["rpc_args"]
                
                # Run task
                self.syslogger.info("Run RPC task: %s " % method_name)
                self.syslogger.debug( "RPC parameter are "+str(param))
                
                func = getattr(self.env["module"],method_name)
                if len(param) == 0:
                    ret = func(callback=self.rpccallback)
                elif len(param) == 1:
                    ret = func(param[0],callback=self.rpccallback)
                elif len(param) == 2:
                    ret = func(param[0],param[1],callback=self.rpccallback)
                elif len(param) == 3:
                    ret = func(param[0],param[1],param[2],callback=self.rpccallback)
                elif len(param) == 4:
                    ret = func(param[0],param[1],param[2],param[3],callback=self.rpccallback)
                elif len(param) == 5:
                    ret = func(param[0],param[1],param[2],param[3],param[4],callback=self.rpccallback)
                elif len(param) == 6:
                    ret = func(param[0],param[1],param[2],param[3],param[4],param[5],callback=self.rpccallback)
                else:
                    raise Exception( "Too many parameters" )
                
                # Add to list for record
                self.rpc_list[request["req_uuid"]] = request
                self.currenttask = request
                # Some of the method might NO need to wait
                if method_name in ["saveGuestOSConf","saveGuestAppConf","reboot","shutdown"]:
                    self.rpccallback(request["req_uuid"],ret)
                    self.currenttask = {}
            
            time.sleep(10)
                    
    def rpccallback(self,task_uuid,ret):
        # Send the respond
        try:
            method_name = self.currenttask["rpc_input"]["rpc_methodname"]
            if method_name in ["createImage","installImage"]:
                 func = getattr(self.env["module"],"getTaskInfo")
                 ret = func("")
                 if ret["result"] == 0:
                     self.proxy = xmlrpclib.ServerProxy(self.conf["rpcbox_url"])
                     self.proxy.RPCUpdateStatus(self.conf["rpcbox_uuid"],self.currenttask["req_uuid"],ret["return"])

            self.syslogger.info("RPC Respond for %s" % self.currenttask["req_uuid"])
            self.syslogger.debug("RPC [%s] Respond: [%s] " % (self.currenttask["req_uuid"],str(ret)))
                        
            self.proxy = xmlrpclib.ServerProxy(self.conf["rpcbox_url"])
            rpcret = self.proxy.RPCRespond(self.conf["rpcbox_uuid"],self.currenttask["req_uuid"],str(ret))
            self.syslogger.debug(rpcret)
        except Exception,e:
            if version[2] == "dev":
                traceback.print_exc()
            self.syslogger.error(str(e))
        # Always set currenttask empty
        self.currenttask = {}
    
if __name__ == "__main__":
    from CloudRainbowConfigure import config
    import pickle

    ret = rawExec(["cat /proc/cmdline |grep -e 'boot_from_iso'"])
    if ret["result"] == 0:
        goToCGI()

    ret = rawExec(["cat /proc/cmdline |grep -e 'auto_install_agent'"])
    if ret["result"] == 0:
        auto_install_agent()

    ret = rawExec(["cat /proc/cmdline |grep -e 'repairagent'"])
    if ret["result"] == 0:
        repairagent()

#    else:
#        goToGuestOS()
 
    def initLogging():
        configure = {"logging":{
            "level":logging.DEBUG,
            "system_log":"/var/log/vfos.sys.log",
            "system_log_level":logging.INFO,
            "system_log_size":10240000,
            "system_backupcount":10,
            }}
        if version[2] == "dev":
            configure["logging"]["system_log_level"] = logging.DEBUG
            
        try:
            
            fd = os.popen("mkdir -p '%s'" % os.path.dirname(configure["logging"]["system_log"]))
            fd.close()
            
            f = open(configure["logging"]["system_log"],"a")
            f.close()
        except Exception,e:
            if version[2] == "dev":
                traceback.print_exc()    
            raise "init logging fail: "+str(e)
            
        # logging initiate
#        if version[2] == "dev":
        logging.basicConfig(level=logging.DEBUG)
    
        syslogger_formatter = logging.Formatter("%(asctime)-15s %(levelname)s %(message)s")
        syslogger_handler = handlers.RotatingFileHandler(configure["logging"]['system_log'],"a",configure["logging"]['system_log_size'],configure["logging"]["system_backupcount"])
        syslogger_handler.setFormatter(syslogger_formatter)
    
        syslogger = logging.getLogger("SYSTEM")
        syslogger.addHandler(syslogger_handler)
        syslogger.setLevel(configure["logging"]['system_log_level'])
        return syslogger

    print "=========================="
    print "Cloud boot init script:"
    print "Version: ",version
    print "=========================="
    print "init logging"
    syslogger = initLogging()
    
    # try to load configure file from local disk

    myip = "";
    print "=========================="
    syslogger.info("Loading configure")
    print "=========================="
    try:
        syslogger.info("Loading configure from disk")
        ret = rawExec([os.path.join(config["shellscriptpath"],"confget.sh") + " " + CloudRainbowPub.getdisktype()+"1"])
        if ret["result"] == 0:
            # CONF_FPATH is defined as a global variable
            
            f = open(CONF_FPATH,"r")
            config = pickle.load(f)
       
            confbox = xmlrpclib.ServerProxy(config["confbox_url"])
            ret2 = confbox.getMyIP()
            myip = ret2["return"]
        else:
			# if there is no configure, then try to broadcast and get configure
            print "please wait for bcast"
            initret = rawExec([os.path.join(config["shellscriptpath"],"bcast_client")+" -f "+os.path.join(config["shellscriptpath"],"bcast_client.conf")])
            print "bcast end",initret["result"],initret["message"];

            if initret["result"] != 0:
                syslogger.error("Get init configure fail:"+saveret["message"])
            else:
                
                bcast_file=os.path.join(config["shellscriptpath"],"cloudboot.ini")

                if os.path.exists(bcast_file):
                    f = open(bcast_file)
                    bcast_msg=lib_json.read(f.read().strip().replace('\'','"'))
                    f.close()

                    if bcast_msg["rpcbox_uuid"] != "":
                        #config.update(pickle.load(f))
                        config.update(bcast_msg)
    
                        f = open(CONF_FPATH,"w")
                        pickle.dump(config,f)
                        f.close()
                        
                        syslogger.info("Save config to disk." )
                        saveret = rawExec([os.path.join(config["shellscriptpath"],"confsave.sh")])
                        
                        if saveret["result"] != 0:
                            syslogger.error("Save to disk error:"+saveret["message"])
                    else:
                        print "invalid config file"

                else:
                    print "cloudboot.ini not found"
            # if there is only configure box configure, then get configure file from the confbox. through tcp
            
        '''
        else:
            
            confbox = xmlrpclib.ServerProxy(config["confbox_url"])
            ret = confbox.getMyIP()
            myip = ret["return"]
            syslogger.debug("my ip: %s" % ret["return"])
            confbox = xmlrpclib.ServerProxy(config["confbox_url"])
            ret = confbox.getMsg(config["confbox_uuid"],myip)
            
            syslogger.info("Load config from net: %s" % str(ret["return"]))
            
            if ret["result"] == 0:
                config.update(ret["return"])
                
                f = open(CONF_FPATH,"w")
                pickle.dump(config,f)
                f.close()
                
                syslogger.info("Save config to disk." )
                saveret = rawExec([os.path.join(config["shellscriptpath"],"confsave.sh")])
                
                if saveret["result"] != 0:
                    syslogger.error("Save to disk error:"+saveret["message"])
            else:
                syslogger.error("Load config from net error:"+ret["message"])
         '''
    except Exception,e:
        print "get configure error"
        if version[2] == "dev":
            traceback.print_exc()
        syslogger.error("Get configuration error:%s" % str(e))

        print "Error,go to GuestOS"
        goToGuestOS()


    # Todo:do network configure

    print config
    print "my foreign ip: " + myip
    print "my local ip:" + getlocalip()

    print "=========================="
    syslogger.info("Getting update information")
    print "=========================="
        
    # update, check version and run update
    try:
        if config["updatebox_url"]:
            updatebox = xmlrpclib.ServerProxy(config["updatebox_url"])
            ret = updatebox.getMsg(config["updatebox_uuid"],distribution)
            syslogger.debug("Update info:"+str(ret))
            if ret["result"] == 0:
                update_info = ret["return"]
                if update_info["version"][0]> version[0]:
                    syslogger.info("Update to version %d.%d " % (update_info["version"][0],update_info["version"][1]))
                    ret = rawExec([os.path.join(config["shellscriptpath"],"update.sh"),update_info["baseurl"]])
                    syslogger.debug(str(ret))
                elif update_info["version"][0]==version[0] and update_info["version"][1] > version[1]:
                    syslogger.info("Update to version %d.%d " % (update_info["version"][0],update_info["version"][1]))
                    ret = rawExec([os.path.join(config["shellscriptpath"],"update.sh"),update_info["baseurl"]])
                    if ret["result"] == 0:
                        syslogger.info("update done")
                    syslogger.debug(str(ret))
    except Exception,e:
        if version[2] == "dev":
            traceback.print_exc()
        syslogger.error("Get update infomation error: %s" % str(e))

    
    print "=========================="
    syslogger.info("Start RPC dispatcher")
    print "=========================="

   
    
    # rpcbox, get task from rpc box, if have task run task [restore or backup or run cgi]
    try:
        cloudrainbow = CloudRainbowAgent.CloudRainbowAgent(config,{"syslogger":syslogger})
        env = {"syslogger":syslogger,
               "module":cloudrainbow}
        try:
            if config["rpcbox_url"]:
                taskmgr = TaskDispatcher(config,env)
        except Exception,e:
            if version[2] == "dev":
                traceback.print_exc()
            syslogger.error("Run task error:%s" % str(e))
    except:
        syslogger.error("Failed to init CloudRainbowAgent.")
   

    print "my foreign ip: " + myip
    print "my local ip:" + getlocalip()
    print "=========================="
    syslogger.info("Getting boot option")
    print "=========================="

    print "have task run task success"
    goToGuestOS()
    exit(0)








        
    # bootbox, change loader
    try:
        if config["bootbox_url"]:
            bootbox = xmlrpclib.ServerProxy(config["bootbox_url"])
            ret = bootbox.getMsg(config["bootbox_uuid"],"cloudboot")
            if ret["result"] == 0:
                boot_info = ret["return"]
                '''
                boot_option = "CGI|DISK"
                '''
                if boot_info["bootoption"].upper() == "DISK":
                    syslogger.info("Boot to disk")
                    rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"disk"])
                elif boot_info["bootoption"].upper() == "CGI":
                    syslogger.info("Boot to cgi")
                    rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"cgi"],False)
            else:
                if version[2] == "dev":
                    syslogger.info("Boot to cgi")
                    rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"cgi"],False)
                else:
                    syslogger.info("Boot to disk")
                    rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"disk"])
        else:
            if version[2] == "dev":
                syslogger.info("Boot to cgi")
                rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"cgi"],False)
            else:
                syslogger.info("Boot to disk")
                rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"disk"])
    except:
        if version[2] == "dev":
            traceback.print_exc()
            rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"cgi"],False)
        else:
            syslogger.info("Boot to disk")
            rawExec([os.path.join(config["shellscriptpath"],"cloudboot.sh"),"disk"])
        
