#!/usr/bin/python
from ftplib import FTP
import copy
import web
import os
import re
import xmlrpclib
import pickle
#from operate import *
try:
    from lib import lib_json as json
except:
    import lib_json as json
import time
from CloudRainbowConfigure import config
import traceback
import StringIO
import subprocess
from CloudRainbowSYS import PCInfo

import math
import random
import CloudRainbowPub

base64EncodeChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
base64DecodeChars = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                     -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                     -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
                     52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
                     -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
                     15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
                     -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
                     41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1]

debugmode = True

#serverURL = "http://192.168.1.215:8080/domain/" 

#serverURL = "http://192.168.1.206:8080/domain/"
serverURL = ""

def runshell(filename):
    #print "run shell:%s" % (config['shellscriptpath']+"/"+filename)
    return os.popen(config['shellscriptpath']+"/"+filename);

def getfilevalue(filename):
    '''return  file content, if file not exist, return ""'''
    content = ""
    if os.path.exists(filename) :
      fp = file(filename)
      content=fp.read()
      fp.close()
    return content.strip()

def checktask():
    ''' Check current task '''
    if os.path.isfile(config['pidfile']):
        pid = getfilevalue(config['pidfile'])
        if os.path.exists("/proc/"+pid.strip()):
            return True
        else:
            return False
    else:
        return False

def rawExec(rcmd):
    '''
    run command and wait command finished.
    @param rcmd: tuple type value for subprocess modules.
    @return: return {"result":0,"return":"","message":""}
        result: 0 for success, none zero for error.
        message: record the stderr if fail
        return: record the stdout if success
    '''
    ret = {"result":0,"return":"","message":""}
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


def base64encode(str):
    '''
    '''
    #var out, i, len;
    #var c1, c2, c3;
    print str
    length = len(str)
    i = 0
    out = ""
    while i < length:
        c1 = ord(unicode(str[i])) & 0xff
        i=i+1
        if i == length:
            out += base64EncodeChars[c1 >> 2]
            out += base64EncodeChars[(c1 & 0x3) << 4]
            out += "=="
            break
        c2 = ord(unicode(str[i]))
        i=i+1
        if i == length:
            out += base64EncodeChars[c1 >> 2]
            out += base64EncodeChars[((c1 & 0x3)<< 4) | ((c2 & 0xF0) >> 4)]
            out += base64EncodeChars[(c2 & 0xF) << 2]
            out += "="
            break
        c3 = ord(unicode(str[i]))
        i=i+1
        out += base64EncodeChars[c1 >> 2]
        out += base64EncodeChars[((c1 & 0x3)<< 4) | ((c2 & 0xF0) >> 4)]
        out += base64EncodeChars[((c2 & 0xF) << 2) | ((c3 & 0xC0) >>6)]
        out += base64EncodeChars[c3 & 0x3F]
        
    return out

def base64decode(str):
    #var c1, c2, c3, c4;
    #var i, len, out;
    length = len(str)
    i = 0
    out = ""
    while i < length:
        #c1
        c1 = base64DecodeChars[ord(unicode(str[i])) & 0xff]
        i=i+1
        while i < length and c1 == -1:
            c1 = base64DecodeChars[ord(unicode(str[i])) & 0xff]
            i=i+1
        
        if c1 == -1:
            break
        #c2
        c2 = base64DecodeChars[ord(unicode(str[i])) & 0xff]
        i=i+1
        while i < len and c2 == -1:
            c2 = base64DecodeChars[ord(unicode(str[i])) & 0xff]
            i=i+1
        
        if c2 == -1:
            break
        
        out += chr((c1 << 2) | ((c2 & 0x30) >> 4));
        #c3
        c3 = ord(unicode(str[i])) & 0xff;
        i=i+1
        if c3 == 61:
            return out
        c3 = base64DecodeChars[c3];        
        while i < len and c3 == -1:
            c3 = ord(unicode(str[i])) & 0xff;
            i=i+1
            if c3 == 61:
                return out
            c3 = base64DecodeChars[c3];
        
        if c3 == -1:
            break
        out += chr(((c2 & 0XF) << 4) | ((c3 & 0x3C) >> 2))
        #c4
        c4 = ord(unicode(str[i])) & 0xff;
        i=i+1
        if c4 == 61:
            return out
        c4 = base64DecodeChars[c4]  
        while i < len and c4 == -1:
            c4 = ord(unicode(str[i])) & 0xff;
            i=i+1
            if c4 == 61:
                return out
            c4 = base64DecodeChars[c4]
        
        if c4 == -1:
            break
        out += chr(((c3 & 0x03) << 6) | c4)

    return out

def encrypt(key, pwd):
    if (pwd == "" or len(pwd) <= 0):
        print "Please enter a password with which to encrypt the message."
        return null

    prand = ""
    for i in range(0, len(pwd)):
        prand += str(ord(unicode(pwd[i])))
                     
    sPos = int(math.floor(len(prand)/5))

    mult = int(prand[sPos] + prand[sPos*2] + prand[sPos*3] + prand[sPos*4])
    incr = math.ceil(len(pwd) / 2)
    modu = pow(2, 31) - 1
    
    if mult < 2:
        print "Algorithm cannot find a suitable hash. Please choose a different password. \nPossible considerations are to choose a more complex or longer password."
        return null
  
    salt = (round(random.random() * 1000000000) % 100000000)
    prand += str(int(salt))
    while len(prand) > 10:
        prand = str(int(prand[0:10]) + int(prand[len(prand)-10:len(prand)]))
  
    prand = (mult * int(prand) + int(incr)) % int(modu)
    enc_chr = ""
    enc_str = ""

    for i in range(0, len(key)):
        enc_chr = int(ord(unicode(key[i])) ^ int(math.floor((prand / float(modu)) * 255)))
        if enc_chr < 16:
            enc_str += "0" + hex(enc_chr).split('x')[-1]
        else:
            enc_str += hex(enc_chr).split('x')[-1]

        prand = (mult * prand + incr) % modu
 

    salt = hex(int(salt)).split('x')[-1]
    while len(salt) < 8:
        salt = "0" + salt
    enc_str += salt
    return enc_str

def decrypt(key, pwd):
    if(key == "" or len(key) < 8):
        print "A salt value could not be extracted from the encrypted message because it's length is too short. The message cannot be decrypted."
        return

    if(pwd == "" or len(pwd) <= 0):
        print "Please enter a password with which to decrypt the message."
        return
    
    prand = ""
    for i in range(0,len(pwd)):
        prand += str(ord(unicode(pwd[i])))
    sPos = int(math.floor(len(prand) / 5))
    mult = int(prand[sPos] + prand[sPos*2] + prand[sPos*3] + prand[sPos*4])
    incr = round(len(pwd) / 2)
    modu = pow(2, 31) - 1 
    salt = int(key[len(key) - 8:len(key)], 16)   
    key = key[0:(len(key) - 8)]   
    prand += str(salt)

    while len(prand) > 10 :
        prand = str(int(prand[0:10]) + int(prand[len(prand)-10:len(prand)]))

    prand = (mult * int(prand) + int(incr)) % int(modu)

    enc_chr = ""
    enc_str = ""

    for i in range(0,len(key),2):
        enc_chr = int(int(key[i:i+2],16) ^ int(math.floor((prand / float(modu)) * 255)))
        enc_str += chr(enc_chr);
        prand = (mult * prand + incr) % modu
    
    return enc_str

def utf16to8(str):
    #var out, i, len, c;
    out = ""
    len = len(str)
    for i in range(0,len):
        c = ord(unicode(str[i]))
        if (c >= 0x0001) and (c <= 0x007F):
            out += str[i]
        elif c > 0x07FF:
            out += chr(0xE0 | ((c >> 12) & 0x0F))
            out += chr(0x80 | ((c >>  6) & 0x3F))
            out += chr(0x80 | ((c >>  0) & 0x3F))
        else:
            out += chr(0xC0 | ((c >>  6) & 0x1F))
            out += chr(0x80 | ((c >>  0) & 0x3F))
    
    return out

def utf8to16(str):
    #var out, i, len, c;
    #var char2, char3;
    out = ""
    len = len(str)
    i = 0
    while i < len:
        c = ord(unicode(str[i]))
        i=i+1
        if 0 == c or 1 == c or 2 == c or 3 == c or 4 == c or 5 == c or 6 == c or 7 == c:
            # 0xxxxxxx
            out += str[i-1]
            break
        elif 12==c or 13==c:
            # 110x xxxx   10xx xxxx
            char2 = ord(unicode(str[i]))
            i=i+1
            out += chr(((c & 0x1F) << 6) | (char2 & 0x3F))
            break
        elif 14==c:
            # 1110 xxxx  10xx xxxx  10xx xxxx
            char2 = ord(unicode(str[i]))
            i=i+1
            char3 = ord(unicode(str[i]))
            i=i+1
            out += chr(((c & 0x0F) << 12) | ((char2 & 0x3F) << 6) | ((char3 & 0x3F) << 0))
            break
        else:
            pass
    return out;
        
class CloudRainbowCGI():
    '''
    related script:
    listimage.sh
    reboot.sh
    
    '''
    def GET(self, name):
        support_method = ["taskinfo","pcinfo","getstatus","getlog","reboot","reboottodisk","installagent","installgrub","repairagent","editMate"]
        if not name in support_method:
            return 'No right to access ' + name + '!'
        try:
            func = getattr(self, name)
            return func()
        except Exception,e:
            return "Error: %s" % e
    
    def POST(self,name):
        support_method = ["createimage","installimage","listimage","register","getregister","activate","login","editMate"]
        if not name in support_method:
            return 'No right to access ' + name + '!'
        try:
            func = getattr(self, name)
            return func()
        except Exception,e:
            return "Error: %s" % e
    
    def editMate(self):
        data = web.input()

        #post to save
        if data.has_key("meta") :
            metaPath="/var/meta"

            meta=data["meta"]
            file_handler = file(metaPath,'w') 
            file_handler.write(json.write(eval(meta),True));
            file_handler.close()

            return "save ok"
        #get to request
        else :
            _dict={}
            metaPath="/var/meta"
            if not os.path.isfile(metaPath):
                #metaPath="/var/meta.conf"
                metaPath="/var/www/lighttpd/meta.conf"
            
            print metaPath
            file_handler = file(metaPath,'r')
            #_dict = eval(json.read(file_handler.read().strip()))
            _dict = json.read(file_handler.read().strip())
            file_handler.close()
            _dict['summary']['production_date'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())

            _listdev = json.read(self.listdev())
            dev2_size = _listdev['return'][-1]['dev_size']
            _dict['hw_requirment']['disk_size'] = dev2_size

            return json.write(_dict)

    def reboottodisk(self):
        shfile = os.path.join(config['shellscriptpath'],"reboottodisk.sh")
        f = subprocess.Popen(["bash",shfile],
                            stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        ret = {"result":0,"return":"rebooting","message":"rebooting"}
        return ret
    
    def installagent(self):
        shfile = os.path.join(config['shellscriptpath'],"install.sh")
        sh = ["bash",shfile,CloudRainbowPub.getdisktype(),"-f"]
        ret = rawExec(sh)
		
        return ret["message"]        
    def installgrub(self):
        shfile = os.path.join(config['shellscriptpath'],"installgrub.sh")
        sh = ["bash",shfile,CloudRainbowPub.getdisktype()]
        ret = rawExec(sh)

		
        return ret["message"]        
    def repairagent(self):
        shfile = os.path.join(config['shellscriptpath'],"repairagent.sh")
        sh = ["bash",shfile,CloudRainbowPub.getdisktype()]
        ret = rawExec(sh)
		
        return ret["message"]        
    def pcinfo(self):
#        '''
#        '''
#        try:
            
        data = web.input(item={})
        pcinfo = PCInfo()
        if data.item == "cpu":
            return pcinfo.getCPUInfo()
        elif data.item == "memory":
            return pcinfo.getMemInfo()
        elif data.item == "disk":
            return pcinfo.getDiskInfo()
        else:
            return "unknow item!"
#        except:
#            return "internal error" 

    def listdev(self):
        '''
        list all of the device of fdisk
        '''
        fd = open("/proc/partitions","r")
        lines = fd.readlines()
        fd.close()

        devs = []
        for line in lines:
            items = line.split()
            if items and items[0].isdigit() and not items[-1].startswith("ram") and items[-2].isdigit() and int(items[-2]) >10 :
                devs.append({"dev_id":items[-1],"dev_size":items[-2]})
                
        return json.write({"result":0,"return":devs,"message":"done"},True)        
    def register(self):
        '''
        register the VM info to agent local and VFOS server
        '''
        global debugmode
        global serverURL
        try:
            if checktask() :
                ret = {'result':1,'message':"Have Task running!"}
            else:
                # parse and check input
                data = web.input(jsonform={})
                jsonform = data.jsonform
                input = json.read(jsonform)
                                
                for checkinput in [input['fm-VMIP'],input['fm-DESCRIPTION'],input['fm-MAC'],input['fm-DOMAIN']]:
                    if "`" in checkinput:
                        ret = {'result':1,'message':"Input error! can not include character '`'. "}
                        return json.write(ret,True)
                
                if ( input['fm-VMIP'].strip()=="" \
                     or input['fm-MAC'].strip()=="" \
                     or input['fm-DOMAIN'].strip()=="" ):
                    ret = {'result':1,'message':"Input error! VM IP or MAC or Domain can not be empty."}
                    return json.write(ret,True)
                 

                client = xmlrpclib.ServerProxy(serverURL)              
                
                #register new VM
                if input['fm-UUID'] == "":
                    vm_info = {"vm_ip":input['fm-VMIP'].strip(),\
                           "vm_description":input['fm-DESCRIPTION'].strip(),\
                           "vm_mac":input['fm-MAC'].strip(),\
                           "domain":input['fm-DOMAIN'].strip(),\
                           "domain_password":input['fm-PASSWORD']}
                    ret = client.safeRegisterVM(vm_info['domain'],vm_info)
                    
                else:#modity VM config
                    vm_info = {"vm_ip":input['fm-VMIP'].strip(),\
                           "vm_description":input['fm-DESCRIPTION'].strip(),\
                           "vm_mac":input['fm-MAC'].strip(),\
                           "vm_uuid":input['fm-UUID'].strip(),\
                           "domain":input['fm-DOMAIN'].strip(),\
                           "domain_password":input['fm-PASSWORD']}
                    ret = client.safeModifyVMConfig(vm_info['domain'],vm_info)                   
                               
                
                if ret['result'] == 0:
                    #copy conf inof from disk to rootfs
                    shfile = os.path.join(config['shellscriptpath'],"confget.sh")
                    sh = ["bash",shfile,CloudRainbowPub.getdisktype()+"1"]
                    ret["debug"] = rawExec(sh)
                    
                    #read config info from rootfs
                    fd = open("/var/cloudrainbow.conf","r")
                    tmp_vm_info = pickle.load(fd)
                    fd.close()
                    
                    #update it and save
                                        
                    tmp_vm_info['domain_mgr_url']=ret['return']['domain_mgr_url']
                    tmp_vm_info['domain']=ret['return']['domain']
                    tmp_vm_info['vm_ip']=ret['return']['vm_ip']
                    tmp_vm_info['vm_mac']=ret['return']['vm_mac']
                    tmp_vm_info['vm_description']=ret['return']['vm_description']
                    tmp_vm_info['vm_uuid']=ret['return']['vm_uuid']
                    tmp_vm_info['confbox_url']=ret['return']['confbox_url']
                    tmp_vm_info['confbox_uuid']=ret['return']['confbox_uuid']
                    tmp_vm_info['rpcbox_url']=ret['return']['rpcbox_url']
                    tmp_vm_info['rpcbox_uuid']=ret['return']['rpcbox_uuid']
                    
                    fd = open("/var/cloudrainbow.conf","w")
                    pickle.dump(tmp_vm_info, fd)
                    fd.close()
                    
                    #copy back to disk
                    shfile = os.path.join(config['shellscriptpath'],"confsave.sh")
                    sh = ["bash",shfile,CloudRainbowPub.getdisktype()+"1"]
                    ret["debug"] = rawExec(sh)         
           
        except:
            if debugmode:
                errf = StringIO.StringIO()
                traceback.print_exc(file=errf)
                emsg = errf.getvalue()
                errf.close()
            else:
                emsg = "Internal error"
            ret = {'result':1,'message':emsg}
            
        return json.write(ret,True)       

    def getregister(self):
        '''
        get register  info of this VM from local
        '''
        global debugmode
        try:
            if checktask() :
                ret = {'result':1,'message':"Can not get VM register info. Have Task running!","debug":""}
            else:
                # parse and check input
                data = web.input(jsonform={})
                jsonform = data.jsonform
                #input = json.read(jsonform)
                
                shfile = os.path.join(config['shellscriptpath'],"confget.sh")
                sh = ["bash",shfile,CloudRainbowPub.getdisktype()+"1"]
                ret = rawExec(sh)
                    
                #read config info from rootfs
                try:
                    fd = open("/var/cloudrainbow.conf","r")
                    tmp_vm_info = pickle.load(fd)
                    fd.close()
                except:
                    import cbootdefconf
                    tmp_vm_info =  cbootdefconf.cboot_config
                    fd2 = open("/var/cloudrainbow.conf","w")
                    pickle.dump(tmp_vm_info, fd2)
                    fd2.close()
                
                ret = {'result':0,'return':tmp_vm_info,'message':"done"}
          
        except:
            if debugmode:
                errf = StringIO.StringIO()
                traceback.print_exc(file=errf)
                emsg = errf.getvalue()
                errf.close()
            else:
                emsg = "Internal error"
            ret = {'result':1,'message':"Can not get VM register info."+emsg}
            
        return json.write(ret,True)
  

    def activate(self):
        '''
        activate this vm 
        '''
        global debugmode
        global serverURL
        try:
            if checktask() :
                ret = {'result':1,'message':"Have Task running!"}
            else:
                # parse and check input
                data = web.input(jsonform={})
                jsonform = data.jsonform
                input = json.read(jsonform)
                                
                for checkinput in [input['fm-UUID'],input['fm-DOMAIN'],input['fm-ASERVER']]:
                    if "`" in checkinput:
                        ret = {'result':1,'message':"Input error! can not include character '`'. "}
                        return json.write(ret,True)
                
                if ( input['fm-UUID'].strip()=="" \
                     or input['fm-ACODE'].strip()=="" \
                     or input['fm-ASERVER'].strip()=="" \
                     or input['fm-DOMAIN'].strip()=="" ):
                    ret = {'result':1,'message':"Input error! Server, Domain ,VM ID, Activate Code can not be empty."}
                    return json.write(ret,True)
                
                
                 
                serverURL = input['fm-ASERVER'].strip()
                client = xmlrpclib.ServerProxy(serverURL)              
                    
                
                vm_info = {"activate_code":input['fm-ACODE'].strip(),\
                      "vm_uuid":input['fm-UUID'].strip(),\
                       "domain":input['fm-DOMAIN'].strip(),\
                       "domain_password":input['fm-PASSWORD']}
                ret = client.activateVM(vm_info)                   
                           
                
                if ret['result'] == 0:
#                    #copy conf inof from disk to rootfs
#                    shfile = os.path.join(config['shellscriptpath'],"confget.sh")
#                    sh = ["bash",shfile,self.getdisktype()+"1"]
#                    ret["debug"] = rawExec(sh)
#                    
#                    #read config info from rootfs
#                    #fd = open("/var/cloudrainbow.conf","r")
#                    tmp_vm_info = pickle.load(fd)
#                    fd.close()
#                    
#                    if (tmp)
#                    
                    #update it and save
                          
                    tmp_vm_info = config                  
                    
                    tmp_vm_info['domain_mgr_url']=ret['return']['domain_mgr_url']
                    tmp_vm_info['domain']=ret['return']['domain']
                    tmp_vm_info['vm_ip']=ret['return']['vm_ip']
                    tmp_vm_info['vm_mac']=ret['return']['vm_mac']
                    tmp_vm_info['vm_description']=ret['return']['vm_description']
                    tmp_vm_info['vm_uuid']=ret['return']['vm_uuid']
                    tmp_vm_info['confbox_url']=ret['return']['confbox_url']
                    tmp_vm_info['confbox_uuid']=ret['return']['confbox_uuid']
                    tmp_vm_info['rpcbox_url']=ret['return']['rpcbox_url']
                    tmp_vm_info['rpcbox_uuid']=ret['return']['rpcbox_uuid']
                    tmp_vm_info['updatebox_url']=ret['return']['updatebox_url']
                    tmp_vm_info['updatebox_uuid']=ret['return']['updatebox_uuid']
                    
                    fd = open("/var/cloudrainbow.conf","w")
                    pickle.dump(tmp_vm_info, fd)
                    fd.close()
                    
                    #copy back to disk
                    shfile = os.path.join(config['shellscriptpath'],"confsave.sh")
                    sh = ["bash",shfile,CloudRainbowPub.getdisktype()+"1"]
                    ret["debug"] = rawExec(sh)         
           
        except:
            if debugmode:
                errf = StringIO.StringIO()
                traceback.print_exc(file=errf)
                emsg = errf.getvalue()
                errf.close()
            else:
                emsg = "Internal error"
            ret = {'result':1,'message':emsg}
            
        return json.write(ret,True)       
    def createimage(self):
        '''
        '''
        global debugmode
        try:
            if checktask() :
                ret = {'result':1,'message':"Have Task running!"}
            else:
                # parse and check input
                data = web.input(jsonform={})
                jsonform = data.jsonform
                input = json.read(jsonform)
                
                backupdisk = input['fm-imgdisk'].lower()
                for checkinput in ['fm-imgname','fm-imgplatform','fm-imgversion','hi-serverip','hi-username','hi-password']:
                    if "`" in checkinput:
                        ret = {'result':1,'message':"Input error! no '`'"}
                        return json.write(ret,True)
                        
#                if not backupdisk in diskinfo.keys():
#                    ret = {'result':1,'message':"disk name should be %s !" % str(diskinfo.keys())}
#                    return json.write(ret,True)
                #tony modify, add key 'fm-template' to make patch
#                if 'fm-template' in input:              
#                    input['fm-imgplatform'] = ""
#                    img_name = input['fm-imgname']+"-"+input['fm-imgversion']
#                    input['fm-md5log']=""
#                if 'fm-template' not in input:
#                    img_name = input['fm-imgname']+"-"+input['fm-imgplatform']+"-"+input['fm-imgversion']                    
#                    input['fm-template'] = ""  
#                                
                #read meta
                _dict={}
                metaPath="/var/meta"
                if not os.path.isfile(metaPath):
                    ret = {"result":1,"return":1,"message":"Please input app information"}
                    return json.write(ret,True)
                
                file_handler = file(metaPath,'r')
                _dict = json.read(file_handler.read().strip())
                file_handler.close()

                #get uuid for task_name and tmp name for file put to ftp
                #shfile = os.path.join(config['shellscriptpath'],"get_uuidgen.sh")
                #sh = ["bash",shfile]
                #ret = rawExec(sh)
                #uuid=ret["return"]

                #print uuid 
                task_option = {
                    "ftp_info":{
                        "host":input['hi-serverip'],
                        "username":input['hi-username'],
                        "password":input['hi-password']
                    },
                    "dev_id":backupdisk,
                    #"task_uuid":"",
                    #"img_type":"BlockFull",
                    #"img_name":"partition2.img",
                    "templatebased":input['fm-template'] if input['hi-radio']=='radiopatch' else '',
                    #"md5log":input['fm-md5log'],
                    "meta":_dict
                 }

                print task_option
                ret = {"result":0,"return":cloudrainbow.createImage(task_option),"message":"Making...Please waiting for a while"}
                #ret = {"result":0,"return":0,"message":"Making...Please waiting for a while"}
                #input uuid or md5

                #upload meta

                
            # parse and format return
        except:
            if debugmode:
                errf = StringIO.StringIO()
                traceback.print_exc(file=errf)
                emsg = errf.getvalue()
                errf.close()
            else:
                emsg = "Internal error"
            ret = {'result':1,'message':emsg}
        return json.write(ret,True)
    
    def saveGuestOS(self,task_uuid,ret):
        '''
        binding with osconfsave.sh to change GuestOS password by user's input
        ''' 
        osconf = {"password":"powerall"}
        #write user password into osconf
        osconf["password"]=self.guestospassword
        try:
            # save to ramdisk with special format
            fd = open("/var/guestos.conf","w")
            kvconf = []
            for k,v in osconf.iteritems():
                kvconf.append("%s=%s\n"%(k.lower(),str(v)))
            fd.writelines(kvconf)
            fd.close()
            
            # call script and save to disk
            saveconf_script = "/var/www/lighttpd/shellscript/osconfsave.sh"
            sh = ["bash",saveconf_script,CloudRainbowPub.getdisktype()+"2"]
            ret = rawExec(sh)
            return ret
        except Exception,e:
            print e
            return ret

    def saveGuestAppConf(self,task_uuid,ret):
        try:
            osconf = {"passwd.py":{"password":"powerall"}}
            #write user password into osconf
            osconf["passwd.py"]["password"]=self.guestospassword

            fd = open("/var/guestos.conf","wb")
            print(osconf)
            pickle.dump(osconf,fd)
            if len(self.guestosappconfig) > 0:
                pickle.dump(self.guestosappconfig,fd)
            fd.close()

            # call script and save to disk
            shfile = os.path.join(config['shellscriptpath'],"osconfsave.sh")        
            sh = ["bash",shfile,CloudRainbowPub.getdisktype()+"2"]                  
            ret = rawExec(sh)  
            
            print ret
            print '----saveGuestAppConf success -----'
            return ret
        except Exception,e:
            print "save configure error: %s" % str(e)
            return {"result":100,"return":"","message":"save configure error: %s" % str(e)}
       
    
    def installimage(self):
        '''
        
        '''
#        def getFtpFileValue(ftpurl):
#            f = subprocess.Popen(["wget",ftpurl,"-O","-"],stdout=subprocess.PIPE)
#            f.wait()            
#            if f.returncode != 0:
#                raise Exception(f.stderr.read())
#            else:
#                return f.stdout.read().strip()

        
        try:
            if checktask() :
                ret = {'result':1,'message':"Have Task running!"}
            else:
                # parse and check input
                data     = web.input(tpl_info={})

                tlp_info     = json.read(data.tpl_info)
                #print "---------------------------------"
                #print tlp_info
                #print "---------------------------------"
                devid = data["fm-recoverdisk"]
                self.guestospassword = data["fm-recoverpassword"]

                # get appconfig dict	(Wonky add)
                self.guestosappconfig = {}
                _appconfig_info = tlp_info["guestos"]["appconfig_info"]
                if len(_appconfig_info) > 0 :
                    for _appconfig in _appconfig_info:
                        if len(_appconfig["configuration"]) > 0:
                            _configs = {}
                            for _config in _appconfig["configuration"]:
                                _configs[_config["name"]] = _config["value"]
                            self.guestosappconfig[_appconfig["appid"]] = _configs
                print self.guestosappconfig,'------------'
            
#                diskinfo = {}

#                for checkinput in ['fm-imgname','fm-recoverdisk','hi_username','hi_serverip']:
#                    if "`" in checkinput:
#                        ret = {'result':1,'message':"Input error!"}
#                        return json.write(ret,True)
#
#                recoverdisk = input["fm-recoverdisk"]
#                if not recoverdisk in diskinfo.keys():
#                    ret = {'result':1,'message':"Input error!"}
#                    return json.write(ret,True)
#                url = "ftp://%(hi_username)s:%(hi_password)s@%(hi_serverip)s/cloudimage/%(fm_imagename)s"%input
#                md5 = getFtpFileValue(url+".md5")
#                size = getFtpFileValue(url+".size")
#tlp_info
#{'guestos': {'os': {'os_password': '123456', 'os_sn': ''}, 'network': {'ip': '', 'netmask': '', 'gateway': ''}, 'appy': {'xxxxx': 'xxx'}, 'appx': {'xxx': 'xx'}}, 'patchinfo': {'patchmd5': '', 'patchsize': '', 'patchname': ''}, 'tplinfo': {'vmmd5log': 'yes', 'vmtpl_type': 'partition,block,full', 'name': 'CentOS-5.2-en-x86_64-tina', 'compatible_vt': ['VTTYPE_XEN3'], 'brief': 'CentOS-5.2-en-x86_64-tina'}, 'vmimg': [{'devid': '', 'image_url': 'ftp://setup:setup@192.168.1.159:21/cloudimage/CentOS-5.2-en-x86_64-tina/hda2', 'patch_url': '', 'md5': 'd9d2315166adb6e69425a1635f32bb2c', 'size': '10528358400'}]}
                if tlp_info["vmimg"][0].has_key("meta_url"):
                    _dict={}
                    meta_url = tlp_info["vmimg"][0]["meta_url"]
                    #sh = ["bash wget  + meta_url + " -P /var/"]
                    subprocess.call(["rm", "-rf", "/var/meta"])
                    subprocess.call(["wget", "-c", meta_url,"-P","/var/"])

                    file_handler = file("/var/meta",'r')
                    _dict = json.read(file_handler.read().strip())
                    file_handler.close()
                    #print _dict


                    task_option = {
                        "img_info":{
                            "img_url":tlp_info["vmimg"][0]["image_url"],
                            "img_md5": _dict["image"]["md5"],
                            "img_size":_dict["hw_requirment"]["disk_size"],
                            "img_type":"",
                            "img_patch_url":tlp_info["vmimg"][0]["patch_url"],
                        },
                        "dev_id":devid,
                        "task_uuid":"",
                        "patch_info":
                        {
                        "img_patch_name":tlp_info["patchinfo"]["patchname"], 
                        "img_patch_md5":tlp_info["patchinfo"]["patchmd5"],   
                        "img_patch_size":tlp_info["patchinfo"]["patchsize"],
                        },                
                    }
                    #print sh
                    #print ret
                    print "comes from TS"
                else:
                    print "comes from ftp"

                    task_option = {
                        "img_info":{
                            "img_url":tlp_info["vmimg"][0]["image_url"],
                            "img_md5":tlp_info["vmimg"][0]["md5"],
                            "img_size":tlp_info["vmimg"][0]["size"],
                            "img_type":"",
                            "img_patch_url":tlp_info["vmimg"][0]["patch_url"],
                        },
                        "dev_id":devid,
                        "task_uuid":"",
                        "patch_info":
                        {
                        "img_patch_name":tlp_info["patchinfo"]["patchname"], 
                        "img_patch_md5":tlp_info["patchinfo"]["patchmd5"],   
                        "img_patch_size":tlp_info["patchinfo"]["patchsize"],
                        },                
                    }
                #print task_option
                #ret = {'result':0,'message':"done"}                
                # main body
                #ret = cloudrainbow.installImage(task_option, callback=self.saveGuestOS)
                #ret = {"result":0,"return":cloudrainbow.installImage(task_option, callback=self.saveGuestOS),"message":"Installing...Please waiting for a while"}
                ret = {"result":0,"return":cloudrainbow.installImage(task_option, callback=self.saveGuestAppConf),"message":"Installing...Please waiting for a while"}
                # parse and format return
                
                #ret = {"result":0,"return":"0","message":"test"}
        except:
            if debugmode:
                errf = StringIO.StringIO()
                traceback.print_exc(file=errf)
                emsg = errf.getvalue()
                errf.close()
            else:
                emsg = "Internal error"
            ret = {'result':1,'message':emsg}
        finally:
            return json.write(ret,True)

    def login(self):
        '''
        '''
        ret = {}
        print "------------------\n"
        #try:
        data = web.input(jsonform={})
        jsonform = data.jsonform
        input   = json.read(jsonform)
        print input
        
        #judge the user and password if it's valid
        encodeuser=input["user"]
        encodepassword=input["pass"]
        encodeuuid=input["uuid"]
        
        #decode the user and password value
        uuid = base64decode(encodeuuid)
        user = decrypt(encodeuser, uuid)
        passwd = decrypt(encodepassword, uuid)
        print "uuid:",uuid,"user:",user,"passwd:",passwd
        
        if user in config.keys():
            if passwd == config[user]:
                #encode user and pass, return
                print "uudi:",uuid
                encodeuuid = encrypt(uuid, uuid)
                #encodeuuid = "1111"
                print "encodeuuid:",encodeuuid
                ret = {'result':0,'message':"ok!","return":{"uuid":encodeuuid}}
            else:
                #password is not valid
                ret = {'result':1,'message':"password is not valid!"}
        else:
            #user is not valid
            ret = {'result':1,'message':"user is not valid!"}
        
        #finally:
        return json.write(ret,True)          

    def taskinfo(self):
        '''
        '''
        return cloudrainbow.getTaskInfo("")        

        
    def listimage(self):
        '''
        '''
        try:
            dirs = []
            #tony add,list the subdirs for patch
            subdirs = []
            tpl_list = []
            def callbackftp(flist):
                ""
                p = re.compile("^d.*")
                for line in flist.split("\n"):
                    if re.match( p, line ):
                        dirs.append(flist.split()[-1])
            def callbacksubdirsftp(flist):
                ""
                p = re.compile("^d.*")
                for line in flist.split("\n"):
                    if re.match( p, line ):
                        subdirs.append(flist.split()[-1])                        
            def _ftplogin(cobj,info):
                try:
                    cobj.connect(info["host"],info["port"]);
                    cobj.login(info["username"],info["password"])
                    #self.cobj.cwd(self.path)
                    return True
                except Exception,ftperr:
                    #self.syslogger.error("login error"+str(ftperr))
                    return False
    
            # get input info
            data = web.input(jsonform={})
            jsonform =     data.jsonform
            #'{"fm-serverip":"192.168.1.177","fm-username":"setup","fm-password":"setup"}'
            input   = json.read(jsonform)
            ftpinfo = {"host":input["fm-serverip"].split(":")[0],
                       "username":input['fm-username'],
                       "password":input["fm-password"],
                       "port":input["fm-serverip"].split(":")[0],
                       "folder":"cloudimage"}
            if len(input["fm-serverip"].split(":")) == 2:
                ftpinfo["port"] = input["fm-serverip"].split(":")[1]
            else:
                ftpinfo["port"] = 21
    
    #            imginfo
            ftp = FTP() 
            print "begin ftp login"
            #return json.write(ret,True)
            if not  _ftplogin(ftp, ftpinfo):
                print "ftp login fail."
                ret ={"result":1,"return":"y","message":"ftp login error"}
                return ""
            
            print "ftp login ok."
            ftp.dir(ftpinfo["folder"],callbackftp)    # list directory contents
            dirs_other = copy.deepcopy(dirs)          # V2.0 Folder
            
            _appconfig = self.getappconfig()
            for dir in dirs:
                meta = copy.deepcopy({
                    "tplinfo":{
                        "name":"centos-5.4-32",
                        "brief":"centos-5.4-32",
                        #"vmtpl_uuid":"1559e458-c7a6-49c2-8f22-c169ebd21997",
                        "compatible_vt":["VTTYPE_XEN3"],
                        "vmtpl_type":"partition,block,full",
                        "vmmd5log":"no",
                    },
                    "guestos":{
                        "appconfig_info":_appconfig,
                        "os":{
                            "os_password":"",
                            "os_sn":""},
                        "network":{
                            "netmask":"",
                            "gateway":"",
                            "ip":""}
                        },
                    "vmimg":[],
                    "patchinfo":[],
                    })
                meta["tplinfo"]["name"] = dir
                meta["tplinfo"]["brief"] = dir
                tempfilelist = ftp.nlst(ftpinfo["folder"]+"/"+dir+"/")
                filelist = []
                # checking
                templist = []
                flag = True #sign if the folder has XXX,XXX.md5,XXX.size
                countflag = False # sign if the folder has at less one  XXX.md5 file
                    
                for file in tempfilelist:
                    if str(file).endswith(".md5"):
                        countflag = True
                        hdaname = str(file)[:str(file).rindex("/")+1]+str(file).split("/")[-1].split(".")[0]
                        if hdaname not in tempfilelist or hdaname+".size" not in tempfilelist:
                            flag = False
                            break
                        else:
                            templist.append(file)
        #                    filelist.append(hdaname)
                            templist.append(hdaname+".size")
                    elif str(file).endswith("patch.tar.gz"):
                        templist.append(file)
                    elif str(file).endswith("templatemd5"):
                        meta["tplinfo"]["vmmd5log"]="yes"
    
                if not flag or not countflag:
                    continue
                else:
                    filelist = copy.deepcopy(templist)
    
                for file in filelist:
                    filepath = "RETR " + file
                    file_handler = StringIO.StringIO()
                    print meta["vmimg"]
                    if str(file).endswith("hda2"):
                        if not meta["vmimg"] or meta["vmimg"] == []:
                            meta["vmimg"].append({})
                            meta["vmimg"][0]["devid"]=hda
                            meta["vmimg"][0]["md5"]=""
                            meta["vmimg"][0]["image_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+hda
                            meta["vmimg"][0]["patch_url"]=""
                            meta["vmimg"][0]["size"]=""                           
                        else:
                            meta["vmimg"][0]["devid"]=hda
                    if str(file).endswith(".md5"):
                        ftp.retrbinary(filepath,file_handler.write)
                        file_handler.seek(0)
                        hda = str(file).split("/")[-1].split(".")[0]
                        if not meta["vmimg"] or meta["vmimg"] == []:
                            meta["vmimg"].append({})
                            meta["vmimg"][0]["devid"]=""
                            meta["vmimg"][0]["md5"]=file_handler.read().strip()
                            meta["vmimg"][0]["image_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+hda
                            meta["vmimg"][0]["patch_url"]=""
                            meta["vmimg"][0]["size"]=""
                        else:                            
                            meta["vmimg"][0]["md5"] = file_handler.read().strip()
                        
                    elif str(file).endswith(".size"):
                        ftp.retrbinary(filepath,file_handler.write)
                        file_handler.seek(0)
                        hda = str(file).split("/")[-1].split(".")[0]
                        if not meta["vmimg"] or meta["vmimg"] == []:
                            meta["vmimg"].append({})
                            meta["vmimg"][0]["devid"]=hda
                            meta["vmimg"][0]["size"]=file_handler.read().strip()
                            meta["vmimg"][0]["image_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+hda
                            meta["vmimg"][0]["patch_url"]=""                            
                            meta["vmimg"][0]["md5"]=""
                        else:
                            meta["vmimg"][0]["size"] = file_handler.read().strip()
                    elif str(file).endswith("patch.tar.gz"):
                        print meta["vmimg"]
                        if not meta["vmimg"] or meta["vmimg"] == []:                        
                            meta["vmimg"].append({})
                            meta["vmimg"][0]["devid"]=""
                            meta["vmimg"][0]["size"]=""
                            meta["vmimg"][0]["md5"]=""
                            meta["vmimg"][0]["image_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+hda
                            meta["vmimg"][0]["patch_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/patch.tar.gz"
                        else:                            
                            meta["vmimg"][0]["patch_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/patch.tar.gz"                        
                           
                    else:
                        pass
                    
                    file_handler.close()
                    file_handler = None
                
                #tony add,
                print "----------------"
                #print ftpinfo["folder"]+"/"+dir
                tempdir = ftpinfo["folder"]+"/"+dir+"/"
                ftp.dir(tempdir,callbacksubdirsftp)
                #print subdirs
                for subdir in subdirs:
                    print tempdir+subdir+"/"
                    tempeachdir = tempdir+subdir+"/"
                    tempfilelist = ftp.nlst(tempeachdir) 
                    print tempfilelist
                                        
                    for file in tempfilelist:
                        filepath = "RETR " + file
                        file_handler = StringIO.StringIO()
                        if str(file).endswith(".md5"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchmd5 = file_handler.read().strip()
                        if str(file).endswith(".size"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchsize = file_handler.read().strip()
                        if str(file).endswith(".type"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchtype = file_handler.read().strip()
                                                
                    meta["patchinfo"].append({"patchname":subdir,
                                  "patchmd5":patchmd5,
                                  "patchsize":patchsize,
                                  "patchtype":patchtype})  
                                                
                subdirs=[]    
                tpl_list.append(meta)
                dirs_other.remove(dir)
            			
            # Cloud Boot V2.0 solution      (Wonky add)
            for dir in dirs_other:
                meta = copy.deepcopy({
                    "tplinfo":{
                        "name":"centos-5.4-32",
                        "brief":"centos-5.4-32",
                        #"vmtpl_uuid":"1559e458-c7a6-49c2-8f22-c169ebd21997",
                        "compatible_vt":["VTTYPE_XEN3"],
                        "vmtpl_type":"partition,block,full",
                        "vmmd5log":"no",
                    },
                    "guestos":{
                        "appconfig_info":_appconfig,
                        "os":{
                            "os_password":"",
                            "os_sn":""},
                        "network":{
                            "netmask":"",
                            "gateway":"",
                            "ip":""}
                        },
                    "vmimg":[],
                    "patchinfo":[],
                    })
                meta["tplinfo"]["name"] = dir
                meta["tplinfo"]["brief"] = dir
                tempfilelist = ftp.nlst(ftpinfo["folder"]+"/"+dir+"/")
                for file in tempfilelist:
                    meta["tplinfo"]["vmmd5log"]="yes"  				
                    if str(file).find("meta") != -1:   #Meta data
                        devid = str(file).split("/")[-1].split(".")[0]
                        filepath = "RETR " + file
                        file_handler = StringIO.StringIO()
                        ftp.retrbinary(filepath,file_handler.write)
                        file_handler.seek(0)
                        meta_jason = file_handler.read().strip()
                        meta_list = json.read(meta_jason)
                                        
                        meta["vmimg"].append({})
                        meta["vmimg"][0]["devid"]=devid
                        meta["vmimg"][0]["size"]=meta_list['hw_requirment']['disk_size']
                        meta["vmimg"][0]["md5"]=meta_list['image']['md5']
                    elif str(file).endswith("img"):
                        img = str(file).split("/")[-1]
                        meta["vmimg"][0]["image_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+img
                    elif str(file).endswith("patch.tar.gz"): 
                        meta["vmimg"][0]["patch_url"]="ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/patch.tar.gz"                   
                    #else:
                        #print file
                print "----------------"
                #print ftpinfo["folder"]+"/"+dir
                tempdir = ftpinfo["folder"]+"/"+dir+"/"
                ftp.dir(tempdir,callbacksubdirsftp)
                for subdir in subdirs:
                    tempeachdir = tempdir+subdir+"/"
                    tempfilelist = ftp.nlst(tempeachdir) 
                                        
                    for file in tempfilelist:
                        filepath = "RETR " + file
                        file_handler = StringIO.StringIO()
                        if str(file).endswith(".md5"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchmd5 = file_handler.read().strip()
                        if str(file).endswith(".size"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchsize = file_handler.read().strip()
                        if str(file).endswith(".type"):
                            ftp.retrbinary(filepath,file_handler.write)
                            file_handler.seek(0)  
                            patchtype = file_handler.read().strip()
                                                
                    meta["patchinfo"].append({"patchname":"ftp://"+ftpinfo["username"]+":"+ftpinfo["password"]+"@"+ftpinfo["host"]+":"+str(ftpinfo["port"])+"/"+ftpinfo["folder"]+"/"+dir+"/"+subdir,
                                  "patchmd5":patchmd5,
                                  "patchsize":patchsize,
                                  "patchtype":patchtype})  
                                                
                subdirs=[]
                tpl_list.append(meta)
                
            ret = {"result":0,"return":tpl_list,"message":"done"}    
        except Exception,e:
            traceback.print_exc(e)
            print e
            ret = {"result":1,"return":[],"message":"Internal error"}
        finally:
            ftp.quit()
            return json.write(ret,True)
    def getappconfig(self):
        #read meta
        _dict={}
        metaPath="/var/meta"
        if not os.path.isfile(metaPath):
            return {}
		
        file_handler = file(metaPath,'r')
        _dict = json.read(file_handler.read().strip())
        file_handler.close() 
        return _dict["appconfig_info"]		

    def getstatus(self):
        '''
        '''
        try:
            if checktask() :
                ret = {'result':1,'message':"Have Task running!"}
            else:
                ret = {'result':0,'message':"Idle!"}
            return json.write(ret,True)
        except:
            return json.write({'result':2,'message':"Internal error!"},True)

    def getlog(self):
        '''
        get log file
        '''
        try:
            if os.path.exists(config['logfile']):
                f = file(config['logfile']);
                info = f.read();
                f.close();
                return info
            else:
                return ""
        except:
            return "internal error"

    def reboot(self):
        '''
        reboot the system
        '''
        if checktask():
            return "have task running. reboot later!"
        lasttask = getfilevalue(config['resultfile'])
        if lasttask == "" or lasttask == "0":
            runshell("reboot.sh")
            return "rebooting...."
        else:
            return "last task fail, please reboot through other method."
    def __checkTask(self):
        '''
        check task status
        '''

        
    
class CloudRainbowRPC():        
    def GET(self,name):
        print ".....", name
        global dispatcher
        web.header('Content-Type', 'text/html')
        print "<body><h1>Error!</h1>"
        print "Method GET is not alowed for XMLRPC requests"
        print "</body>"
        return ""
    def POST(self,name=""):
        global dispatcher
        response = dispatcher._marshaled_dispatch(web.webapi.data())
        web.header('Content-length', str(len(response)))
        print response
        return response

class Error():
    def GET(self,name=""):
        return "not support %s"%name
    def POST(self,name=""):
        return "not support %s"%name
class Common:
    def GET(self,name):
        
        try:
            response = open(os.path.join(basepath,name),"r").read()
            suffix = os.path.basename(name).split(".")[-1]
            if suffix in mimesuffix:
                web.header('Content-type', mimesuffix[suffix])
                
        except:
            traceback.print_exc()
            response = '''<body><h1>Error!</h1>
        Get file [%s] fail
        </body>''' % name
        web.header('Content-length', str(len(response)))
        return response

    def POST(self,name=""):
        web.header('Content-Type', 'text/html')
        respone = '''<body><h1>Error!</h1>
        Method GET is not allowed for JSONRPC requests
        </body>'''
        return respone

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
dispatcher = SimpleXMLRPCDispatcher(allow_none = False, encoding = "UTF-8")

from CloudRainbowAgent import CloudRainbowAgent
cloudrainbow = CloudRainbowAgent(config)
dispatcher.register_instance(cloudrainbow)

if __name__ == "__main__":
    # use parameter to control, if we should start the cgi interface or just rpc interface
    
    urls = (
        '/cgi/(.*)','CloudRainbowCGI',
        '/rpc/(.*)', 'CloudRainbowRPC',
        '/(.*)','Common'
    )
#    from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
#    dispatcher = SimpleXMLRPCDispatcher(allow_none = False, encoding = "UTF-8")
#    
#    from CloudRainbowAgent import CloudRainbowAgent
#    cloudrainbow = CloudRainbowCGI(config)
#    dispatcher.register_instance(cloudrainbow)
    mimesuffix={
            "123":"application/vnd.lotus-1-2-3",
            "3gp":"video/3gpp",
            "aab":"application/x-authoware-bin",
            "aam":"application/x-authoware-map",
            "aas":"application/x-authoware-seg",
            "ai":"application/postscript",
            "aif":"audio/x-aiff",
            "aifc":"audio/x-aiff",
            "aiff":"audio/x-aiff",
            "als":"audio/X-Alpha5",
            "amc":"application/x-mpeg",
            "ani":"application/octet-stream",
            "asc":"text/plain",
            "asd":"application/astound",
            "asf":"video/x-ms-asf",
            "asn":"application/astound",
            "asp":"application/x-asap",
            "asx":"video/x-ms-asf",
            "au":"audio/basic",
            "avb":"application/octet-stream",
            "avi":"video/x-msvideo",
            "awb":"audio/amr-wb",
            "bcpio":"application/x-bcpio",
            "bin":"application/octet-stream",
            "bld":"application/bld",
            "bld2":"application/bld2",
            "bmp":"application/x-MS-bmp",
            "bpk":"application/octet-stream",
            "bz2":"application/x-bzip2",
            "cal":"image/x-cals",
            "ccn":"application/x-cnc",
            "cco":"application/x-cocoa",
            "cdf":"application/x-netcdf",
            "cgi":"magnus-internal/cgi",
            "chat":"application/x-chat",
            "class":"application/octet-stream",
            "clp":"application/x-msclip",
            "cmx":"application/x-cmx",
            "co":"application/x-cult3d-object",
            "cod":"image/cis-cod",
            "cpio":"application/x-cpio",
            "cpt":"application/mac-compactpro",
            "crd":"application/x-mscardfile",
            "csh":"application/x-csh",
            "csm":"chemical/x-csml",
            "csml":"chemical/x-csml",
            "css":"text/css",
            "cur":"application/octet-stream",
            "dcm":"x-lml/x-evm",
            "dcr":"application/x-director",
            "dcx":"image/x-dcx",
            "dhtml":"text/html",
            "dir":"application/x-director",
            "dll":"application/octet-stream",
            "dmg":"application/octet-stream",
            "dms":"application/octet-stream",
            "doc":"application/msword",
            "dot":"application/x-dot",
            "dvi":"application/x-dvi",
            "dwf":"drawing/x-dwf",
            "dwg":"application/x-autocad",
            "dxf":"application/x-autocad",
            "dxr":"application/x-director",
            "ebk":"application/x-expandedbook",
            "emb":"chemical/x-embl-dl-nucleotide",
            "embl":"chemical/x-embl-dl-nucleotide",
            "eps":"application/postscript",
            "eri":"image/x-eri",
            "es":"audio/echospeech",
            "esl":"audio/echospeech",
            "etc":"application/x-earthtime",
            "etx":"text/x-setext",
            "evm":"x-lml/x-evm",
            "evy":"application/x-envoy",
            "exe":"application/octet-stream",
            "fh4":"image/x-freehand",
            "fh5":"image/x-freehand",
            "fhc":"image/x-freehand",
            "fif":"image/fif",
            "fm":"application/x-maker",
            "fpx":"image/x-fpx",
            "fvi":"video/isivideo",
            "gau":"chemical/x-gaussian-input",
            "gca":"application/x-gca-compressed",
            "gdb":"x-lml/x-gdb",
            "gif":"image/gif",
            "gps":"application/x-gps",
            "gtar":"application/x-gtar",
            "gz":"application/x-gzip",
            "hdf":"application/x-hdf",
            "hdm":"text/x-hdml",
            "hdml":"text/x-hdml",
            "hlp":"application/winhlp",
            "hqx":"application/mac-binhex40",
            "htm":"text/html",
            "html":"text/html",
            "hts":"text/html",
            "ice":"x-conference/x-cooltalk",
            "ico":"application/octet-stream",
            "ief":"image/ief",
            "ifm":"image/gif",
            "ifs":"image/ifs",
            "imy":"audio/melody",
            "ins":"application/x-NET-Install",
            "ips":"application/x-ipscript",
            "ipx":"application/x-ipix",
            "it":"audio/x-mod",
            "itz":"audio/x-mod",
            "ivr":"i-world/i-vrml",
            "j2k":"image/j2k",
            "jad":"text/vnd.sun.j2me.app-descriptor",
            "jam":"application/x-jam",
            "jar":"application/java-archive",
            "jnlp":"application/x-java-jnlp-file",
            "jpe":"image/jpeg",
            "jpeg":"image/jpeg",
            "jpg":"image/jpeg",
            "jpz":"image/jpeg",
            "js":"application/x-javascript",
            "jwc":"application/jwc",
            "kjx":"application/x-kjx",
            "lak":"x-lml/x-lak",
            "latex":"application/x-latex",
            "lcc":"application/fastman",
            "lcl":"application/x-digitalloca",
            "lcr":"application/x-digitalloca",
            "lgh":"application/lgh",
            "lha":"application/octet-stream",
            "lml":"x-lml/x-lml",
            "lmlpack":"x-lml/x-lmlpack",
            "lsf":"video/x-ms-asf",
            "lsx":"video/x-ms-asf",
            "lzh":"application/x-lzh",
            "m13":"application/x-msmediaview",
            "m14":"application/x-msmediaview",
            "m15":"audio/x-mod",
            "m3u":"audio/x-mpegurl",
            "m3url":"audio/x-mpegurl",
            "ma1":"audio/ma1",
            "ma2":"audio/ma2",
            "ma3":"audio/ma3",
            "ma5":"audio/ma5",
            "man":"application/x-troff-man",
            "map":"magnus-internal/imagemap",
            "mbd":"application/mbedlet",
            "mct":"application/x-mascot",
            "mdb":"application/x-msaccess",
            "mdz":"audio/x-mod",
            "me":"application/x-troff-me",
            "mel":"text/x-vmel",
            "mi":"application/x-mif",
            "mid":"audio/midi",
            "midi":"audio/midi",
            "mif":"application/x-mif",
            "mil":"image/x-cals",
            "mio":"audio/x-mio",
            "mmf":"application/x-skt-lbs",
            "mng":"video/x-mng",
            "mny":"application/x-msmoney",
            "moc":"application/x-mocha",
            "mocha":"application/x-mocha",
            "mod":"audio/x-mod",
            "mof":"application/x-yumekara",
            "mol":"chemical/x-mdl-molfile",
            "mop":"chemical/x-mopac-input",
            "mov":"video/quicktime",
            "movie":"video/x-sgi-movie",
            "mp2":"audio/x-mpeg",
            "mp3":"audio/x-mpeg",
            "mp4":"video/mp4",
            "mpc":"application/vnd.mpohun.certificate",
            "mpe":"video/mpeg",
            "mpeg":"video/mpeg",
            "mpg":"video/mpeg",
            "mpg4":"video/mp4",
            "mpga":"audio/mpeg",
            "mpn":"application/vnd.mophun.application",
            "mpp":"application/vnd.ms-project",
            "mps":"application/x-mapserver",
            "mrl":"text/x-mrml",
            "mrm":"application/x-mrm",
            "ms":"application/x-troff-ms",
            "mts":"application/metastream",
            "mtx":"application/metastream",
            "mtz":"application/metastream",
            "mzv":"application/metastream",
            "nar":"application/zip",
            "nbmp":"image/nbmp",
            "nc":"application/x-netcdf",
            "ndb":"x-lml/x-ndb",
            "ndwn":"application/ndwn",
            "nif":"application/x-nif",
            "nmz":"application/x-scream",
            "nokia-op-logo":"image/vnd.nok-oplogo-color",
            "npx":"application/x-netfpx",
            "nsnd":"audio/nsnd",
            "nva":"application/x-neva1",
            "oda":"application/oda",
            "oom":"application/x-AtlasMate-Plugin",
            "pac":"audio/x-pac",
            "pae":"audio/x-epac",
            "pan":"application/x-pan",
            "pbm":"image/x-portable-bitmap",
            "pcx":"image/x-pcx",
            "pda":"image/x-pda",
            "pdb":"chemical/x-pdb",
            "pdf":"application/pdf",
            "pfr":"application/font-tdpfr",
            "pgm":"image/x-portable-graymap",
            "pict":"image/x-pict",
            "pm":"application/x-perl",
            "pmd":"application/x-pmd",
            "png":"image/png",
            "pnm":"image/x-portable-anymap",
            "pnz":"image/png",
            "pot":"application/vnd.ms-powerpoint",
            "ppm":"image/x-portable-pixmap",
            "pps":"application/vnd.ms-powerpoint",
            "ppt":"application/vnd.ms-powerpoint",
            "pqf":"application/x-cprplayer",
            "pqi":"application/cprplayer",
            "prc":"application/x-prc",
            "proxy":"application/x-ns-proxy-autoconfig",
            "ps":"application/postscript",
            "ptlk":"application/listenup",
            "pub":"application/x-mspublisher",
            "pvx":"video/x-pv-pvx",
            "qcp":"audio/vnd.qcelp",
            "qt":"video/quicktime",
            "qti":"image/x-quicktime",
            "qtif":"image/x-quicktime",
            "r3t":"text/vnd.rn-realtext3d",
            "ra":"audio/x-pn-realaudio",
            "ram":"audio/x-pn-realaudio",
            "rar":"application/x-rar-compressed",
            "ras":"image/x-cmu-raster",
            "rdf":"application/rdf+xml",
            "rf":"image/vnd.rn-realflash",
            "rgb":"image/x-rgb",
            "rlf":"application/x-richlink",
            "rm":"audio/x-pn-realaudio",
            "rmf":"audio/x-rmf",
            "rmm":"audio/x-pn-realaudio",
            "rmvb":"audio/x-pn-realaudio",
            "rnx":"application/vnd.rn-realplayer",
            "roff":"application/x-troff",
            "rp":"image/vnd.rn-realpix",
            "rpm":"audio/x-pn-realaudio-plugin",
            "rt":"text/vnd.rn-realtext",
            "rte":"x-lml/x-gps",
            "rtf":"application/rtf",
            "rtg":"application/metastream",
            "rtx":"text/richtext",
            "rv":"video/vnd.rn-realvideo",
            "rwc":"application/x-rogerwilco",
            "s3m":"audio/x-mod",
            "s3z":"audio/x-mod",
            "sca":"application/x-supercard",
            "scd":"application/x-msschedule",
            "sdf":"application/e-score",
            "sea":"application/x-stuffit",
            "sgm":"text/x-sgml",
            "sgml":"text/x-sgml",
            "sh":"application/x-sh",
            "shar":"application/x-shar",
            "shtml":"magnus-internal/parsed-html",
            "shw":"application/presentations",
            "si6":"image/si6",
            "si7":"image/vnd.stiwap.sis",
            "si9":"image/vnd.lgtwap.sis",
            "sis":"application/vnd.symbian.install",
            "sit":"application/x-stuffit",
            "skd":"application/x-Koan",
            "skm":"application/x-Koan",
            "skp":"application/x-Koan",
            "skt":"application/x-Koan",
            "slc":"application/x-salsa",
            "smd":"audio/x-smd",
            "smi":"application/smil",
            "smil":"application/smil",
            "smp":"application/studiom",
            "smz":"audio/x-smd",
            "snd":"audio/basic",
            "spc":"text/x-speech",
            "spl":"application/futuresplash",
            "spr":"application/x-sprite",
            "sprite":"application/x-sprite",
            "spt":"application/x-spt",
            "src":"application/x-wais-source",
            "stk":"application/hyperstudio",
            "stm":"audio/x-mod",
            "sv4cpio":"application/x-sv4cpio",
            "sv4crc":"application/x-sv4crc",
            "svf":"image/vnd",
            "svg":"image/svg-xml",
            "svh":"image/svh",
            "svr":"x-world/x-svr",
            "swf":"application/x-shockwave-flash",
            "swfl":"application/x-shockwave-flash",
            "t":"application/x-troff",
            "tad":"application/octet-stream",
            "talk":"text/x-speech",
            "tar":"application/x-tar",
            "taz":"application/x-tar",
            "tbp":"application/x-timbuktu",
            "tbt":"application/x-timbuktu",
            "tcl":"application/x-tcl",
            "tex":"application/x-tex",
            "texi":"application/x-texinfo",
            "texinfo":"application/x-texinfo",
            "tgz":"application/x-tar",
            "thm":"application/vnd.eri.thm",
            "tif":"image/tiff",
            "tiff":"image/tiff",
            "tki":"application/x-tkined",
            "tkined":"application/x-tkined",
            "toc":"application/toc",
            "toy":"image/toy",
            "tr":"application/x-troff",
            "trk":"x-lml/x-gps",
            "trm":"application/x-msterminal",
            "tsi":"audio/tsplayer",
            "tsp":"application/dsptype",
            "tsv":"text/tab-separated-values",
            "tsv":"text/tab-separated-values",
            "ttf":"application/octet-stream",
            "ttz":"application/t-time",
            "txt":"text/plain",
            "ult":"audio/x-mod",
            "ustar":"application/x-ustar",
            "uu":"application/x-uuencode",
            "uue":"application/x-uuencode",
            "vcd":"application/x-cdlink",
            "vcf":"text/x-vcard",
            "vdo":"video/vdo",
            "vib":"audio/vib",
            "viv":"video/vivo",
            "vivo":"video/vivo",
            "vmd":"application/vocaltec-media-desc",
            "vmf":"application/vocaltec-media-file",
            "vmi":"application/x-dreamcast-vms-info",
            "vms":"application/x-dreamcast-vms",
            "vox":"audio/voxware",
            "vqe":"audio/x-twinvq-plugin",
            "vqf":"audio/x-twinvq",
            "vql":"audio/x-twinvq",
            "vre":"x-world/x-vream",
            "vrml":"x-world/x-vrml",
            "vrt":"x-world/x-vrt",
            "vrw":"x-world/x-vream",
            "vts":"workbook/formulaone",
            "wav":"audio/x-wav",
            "wax":"audio/x-ms-wax",
            "wbmp":"image/vnd.wap.wbmp",
            "web":"application/vnd.xara",
            "wi":"image/wavelet",
            "wis":"application/x-InstallShield",
            "wm":"video/x-ms-wm",
            "wma":"audio/x-ms-wma",
            "wmd":"application/x-ms-wmd",
            "wmf":"application/x-msmetafile",
            "wml":"text/vnd.wap.wml",
            "wmlc":"application/vnd.wap.wmlc",
            "wmls":"text/vnd.wap.wmlscript",
            "wmlsc":"application/vnd.wap.wmlscriptc",
            "wmlscript":"text/vnd.wap.wmlscript",
            "wmv":"audio/x-ms-wmv",
            "wmx":"video/x-ms-wmx",
            "wmz":"application/x-ms-wmz",
            "wpng":"image/x-up-wpng",
            "wpt":"x-lml/x-gps",
            "wri":"application/x-mswrite",
            "wrl":"x-world/x-vrml",
            "wrz":"x-world/x-vrml",
            "ws":"text/vnd.wap.wmlscript",
            "wsc":"application/vnd.wap.wmlscriptc",
            "wv":"video/wavelet",
            "wvx":"video/x-ms-wvx",
            "wxl":"application/x-wxl",
            "x-gzip":"application/x-gzip",
            "xar":"application/vnd.xara",
            "xbm":"image/x-xbitmap",
            "xdm":"application/x-xdma",
            "xdma":"application/x-xdma",
            "xdw":"application/vnd.fujixerox.docuworks",
            "xht":"application/xhtml+xml",
            "xhtm":"application/xhtml+xml",
            "xhtml":"application/xhtml+xml",
            "xla":"application/vnd.ms-excel",
            "xlc":"application/vnd.ms-excel",
            "xll":"application/x-excel",
            "xlm":"application/vnd.ms-excel",
            "xls":"application/vnd.ms-excel",
            "xlt":"application/vnd.ms-excel",
            "xlw":"application/vnd.ms-excel",
            "xm":"audio/x-mod",
            "xml":"text/xml",
            "xmz":"audio/x-mod",
            "xpi":"application/x-xpinstall",
            "xpm":"image/x-xpixmap",
            "xsit":"text/xml",
            "xsl":"text/xml",
            "xul":"text/xul",
            "xwd":"image/x-xwindowdump",
            "xyz":"chemical/x-pdb",
            "yz1":"application/x-yz1",
            "z":"application/x-compress",
            "zac":"application/x-zaurus-zac",
            "zip":"application/zip"
        }

    basepath = "/var/www/lighttpd/html"
    app = web.application(urls, globals())
    web.config.debug = True
    app.run()

