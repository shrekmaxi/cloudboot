# -*- coding: utf-8 -*-
'''
Created on 2010-12-28
## Copyright (C) 2007-2010 The PowerallNetworks
## See LICENSE for details
##----------------------------------------------------------------------
'''
import subprocess
import xmlrpclib
import os
import pickle

class PCInfo():
    '''
    use in linux environment for cloud rainbow
    '''
    def __init__(self):
        self.getAllRawPCInfo()
    def getMemInfo(self):
        return self.raw_mem_info
    def getCPUInfo(self):
        return self.raw_cpu_info
    def getDiskInfo(self):
        return self.raw_disk_info
    
    def __getMemInfo(self):
        f = open("/proc/meminfo","r")
        self.raw_mem_info = f.read()
        f.close()
    
    def __getCPUInfo(self):
        f = open("/proc/cpuinfo","r")
        self.raw_cpu_info = f.read()
        f.close()
    
    def __getDiskInfo(self):
        f = open("/proc/partitions","r")
        self.raw_disk_info = f.read()
        f.close()

    def getAllRawPCInfo(self):
        self.__getCPUInfo()
        self.__getDiskInfo()
        self.__getMemInfo()
        
class Configure():
    def __init__(self):
        '''
        
        '''
        self.conf_filename = ""
        self.default_conf = {
                "conf_filename":"cloudrainbow.conf",
                "conf_file":"/var/cloudrainbow.conf",
                "script_path":"/var/www/lighttpd/cgi/shellscript",
                "message_box":{"uuid":"","url":""},
                "rpc_box":{"uuid":"","url":""},
                "network":{
                    "ip":"192.168.1.164",
                    "type":"static",
                    "nic":"eth0",
                    "netmask":"255.255.255.0",
                    "gateway":"192.168.1.254",
                    "dns":"8.8.8.8",
                }
            }
    
    def __getMac(self):
        '''
        get mac from 
        '''
        try:
            f = os.popen("ifconfig eth0 | grep HWaddr")
            tmpstr = f.read()
            mac = tmpstr.split()[-1].strip()
            return mac
        except:
            return ""
        
    def __exec(self,rcmd):
        '''
        run command and wait command finished.
        @param rcmd: tuple type value for subprocess modules.
        @return: return {"result":0,"return":"","message":""}
            result: 0 for success, none zero for error.
            message: record the stderr if fail
            return: record the stdout if success
        '''
        ret = {"result":0,"return":"","message":""}
        if self.debug:
            print rcmd
        f = subprocess.Popen(rcmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        f.wait()
        
        if f.returncode != 0:
            ret["message"] = f.stderr.read()
            ret["result"] = f.returncode
        else:
            ret["message"] = "done"
            ret["result"] = 0
            ret["return"] = f.stdout.read()
            
        return ret;
        
    def __getConfFromDisk(self):
        '''
        @requires: confget.sh
        run the script of get local configure from the disk, set to the 
        @return: True if success else return False
        '''
        try:
        # get the partition id
            peersh = "confget.sh"
            confsh = os.path.join(self.default_conf["script_path"],peersh)
            conf_file = self.default_conf["conf_file"]
            
            if not os.path.exists(conf_file):
                return False
            # detect the file system from partition flag
            if os.path.exists(conf_file):
                f=open(conf_file,"r")
                self.config = pickle.load(f)
                f.close()
                return True
            else:
                return False
        except:
            return False    
        # mount the file system and try to get the configure file from the disk 
        
        
    def __configNetwork(self):
        '''
        
        '''
        
    def __configInfo(self):
        '''
        
        '''
        
    def __getConfFromNet(self):
        '''
        
        '''
        try:
            proxy = xmlrpclib.server(self.default_conf["message_box"])
            ret = proxy.getMsg("configure")
            if ret["result"] == 0:
                self.config = ret["return"]
                return True
            else:
                return False
        except:
            return False
                
    def __getConfFromKernelCmd(self):
        '''
        peer script: confcmdget        
        '''
    def saveToDisk(self):
        '''
        @requires: confsave.sh
        '''
        conf_file = self.default_conf["conf_file"]
        try:
            # save to ramdisk
            f=open(conf_file,"w")
            pickle.dump(self.config,f)
            f.close()
            # save to local disk
            peersh = "confget.sh"
            confsh = os.path.join(self.default_conf["script_path"],peersh)
            ret = self.__exec(["bash",confsh])
            if ret["result"] == 0:
                return True
            else:
                return False
        except:
            return False
        
    def saveToNet(self):
        '''
        @requires: confsave.sh
        '''
        try:
            proxy = xmlrpclib.server(self.default_conf["message_box"])
            ret = proxy.setMessage("configure",self.config)
            return ret["result"] == 0
        except:
            return False

class TaskRouter():
    def __init__(self):
        '''

        '''
    
    def getTask(self):
        '''
        
        '''
        # get task
        
        # run task
        
    def callback_Install_finished(self):
        '''
        
        '''
    
    def callback_install_status(self):
        '''
        
        '''
        
    def callback_backup_finished(self):
        '''
        
        '''
    
    def callback_backup_status(self):
        '''
        
        '''
        
    def callback_update_finished(self):
        '''
        
        '''
        
class Update():
    def __init__(self):
        '''
        
        '''
    
    def __runUpdate(self):
        '''
        
        '''
        
    def getCurrentVersion(self):
        '''
    
        '''
    
class Reboot():
    def __init__(self):
        '''
        
        '''
    def rebootToDisk(self):    
        '''
        
        '''
    
    def reboot(self):
        '''
        
        '''
        
class FTPTplLib():
    def __init__(self):
        '''
        
        '''
    