import os
import copy
from uuid import uuid4
import subprocess
import threading
import logging
from logging import handlers
from VFOSERR import VFOSERR
import pickle as p
import CloudRainbowPub
from ftplib import FTP

try:
    from lib import lib_json as json
except:
    import lib_json as json


STATUS_END = "STATUS_END"
STATUS_NOTSTART = "STATUS_NOTSTART"
STATUS_BUSY = "STATUS_BUSY"

RESULT_SUCCESS = "RESULT_SUCCESS"
RESULT_FAIL = "RESULT_FAIL"
RESULT_UNKNOW = "RESULT_UNKNOW"
RESULT_NONE = "RESULT_NONE"
 
def getFileValue(file_path):
    if os.path.isfile(file_path):
        return open(file_path,"r").read().strip()
    else:
        return ""
    

def rawExec(rcmd, boolwait=True):
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
    if boolwait:
        f.wait()
    
    if f.returncode != 0:
        ret["message"] = f.stderr.read()
        ret["result"] = f.returncode
    else:
        ret["message"] = "done"
        ret["result"] = 0
        ret["return"] = f.stdout.read()
        
    return ret;


class CloudRainbowAgent():
    '''
    use to install the image from the web to the disk, a demo service
    or to create image from the local disk to the web
    '''
    def __init__(self,configure,env={}):
        '''
        configure = {
            "taskinfopath":"",
            "historytaskpath":"",
            "schellscriptpath":"",
            "debug":""
        }
        '''
        self.conf = configure
        self.__init__logging()
        self.__checking__()
        self.__init__schema()
        self.__init__tasklist()
    
    def helloworld(self):
        '''
        
        '''
        return {"return":"hello world","result":0,"message":"done"}    
    def __init__schema(self):
        '''
        initiate the schema
        '''
        self.schema = {
            "schema_install_option":{
                "img_info":{
                    "img_url":"",
                    "img_md5":"",
                    "img_size":"",
                    "img_type":""
                },
                "dev_id":"hda",
                "task_uuid":""
            },
            "schema_create_option":{
                "ftp_info":{
                    "host":"",
                    "username":"",
                    "password":""
                },
                "dev_id":"hda",
                "task_uuid":"",
                "img_type":"",
                "img_name":""
            },
            "schema_progress_info":{
                "status":STATUS_END,
                "result":RESULT_NONE,
                "progress":20,
                "message":"time elapse: 101 second",
                "debugmessage":""
            },
            "schema_task_info":{
                "task_uuid":"",
                "task_key":str(uuid4()),
                "task_type":"Create_Image",
                "status":STATUS_NOTSTART,
                "result":RESULT_NONE,
                "task_option":{},
                "task_progress":{
                    "status":STATUS_END,
                    "result":RESULT_NONE,
                    "progress":20,
                    "message":"time elapse: 101 second",
                    "debugmessage":""}
            },
            "schema_ret":{
                "return":"",
                "result":0,
                "message":""
            },
            "schema_uuid":"XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX"
        }
            
    def __init__logging(self):
        configure = {"logging":{
            "level":logging.DEBUG,
            "system_log":"/var/log/vfos.sys.log",
            "system_log_level":logging.DEBUG,
            "system_log_size":10240000,
            "system_backupcount":10,
            }}
        try:
            f = open(configure["logging"]["system_log"],"a")
            f.close()
        except Exception,e:
            raise "init logging fail: "
            
        # logging initiate
        logging.basicConfig(level=logging.DEBUG)

        syslogger_formatter = logging.Formatter("%(asctime)-15s %(levelname)s %(message)s")
        syslogger_handler = handlers.RotatingFileHandler(configure["logging"]['system_log'],"a",configure["logging"]['system_log_size'],configure["logging"]["system_backupcount"])
        syslogger_handler.setFormatter(syslogger_formatter)

        self.syslogger = logging.getLogger("SYSTEM")
        self.syslogger.addHandler(syslogger_handler)
        self.syslogger.setLevel(configure["logging"]['system_log_level'])
        
    def __init__tasklist(self):    
        '''
        initiate the tasklist
        '''
        self.task_list = {}
        self.current_task_uuid = ""
        
    def __checking__(self):
        '''
        checking if the environment is healthy when initiation.
        @return: True for everything OK, else raise exception
        '''

        # check folder
        folder_name = ["taskinfopath","historytaskpath"]
        for path in folder_name:
            if not os.path.exists(self.conf[path]):
                os.mkdir(self.conf[path])

		#check shellscriptpath
        if not os.path.exists(self.conf['shellscriptpath']):
                raise VFOSERR("Configure error: %s not exit" % self.conf["shellscriptpath"], VFOSERR.ERR_CON_FS_NOTEXIST)
                
        script_name = ["disk_restore.srv.sh","disk_backup.srv.sh"]
        for sh in script_name:
            if not os.path.exists(os.path.join(self.conf["shellscriptpath"],sh)):
                raise VFOSERR("configure error: some file [%s] not exist" % os.path.join(self.conf["shellscriptpath"],sh),VFOSERR.ERR_CON_FS_NOTEXIST)
        return True
        # check 
        
    def __checkDevice(self,device_id):    
        '''
        check if device id exist,
        reference of "http://www.kernel.org/pub/linux/docs/device-list/devices.txt"
        @param device_id: eg:hd* or sd*
        @type device_id:
        @return: True if device id exist else False
        '''
        if not device_id.startswith("sd") and not device_id.startswith("hd") and not device_id.startswith("xv"):
            return False
        
        return os.path.exists("/dev/"+device_id)
    
    def __getDeviceSize(self,device_id):        
        '''
        get device size from /proc/partitions
        @param device_id:
        @type device_id:
        @return: device size
        @rtype: long
        @raise ERR_INPUT_IDNOTEXIST: device not exist
        '''
        f = open("/proc/partitions","r")
        lines = f.readlines()
        devline = [line for line in lines if line.endswith("%s\n" % device_id)]
        if not len(devline) == 1:
            raise VFOSERR("device [%s] not exist" % device_id,VFOSERR.ERR_INPUT_IDNOTEXIST)
        dev_info = devline[0].split()
        dev_size = long(dev_info[2])*1024
        f.close()
        return dev_size    
        
    def installImage(self,task_option,**kwargs):
        '''
        download and install the disk from the web server[ftp,http,https], as the task should take a long time, 
        so the task would run in background and return a task uuid.
        @param task_option:  
                task_option:{
                    "img_info":{
                        "img_url":"",
                        "img_md5":"",
                        "img_size":"",
                        "img_type":""
                    },
                    "dev_id":"hda",
                    "task_uuid":""
                }
        @type task_option: schema_install_option 
        @return: task_uuid
        @rtype: schema_uuid
        @raise ERR_CON_STATUS_BUSY: have task running
        @raise ERR_INPUT_IDEXIST: task id exist
        @raise ERR_INPUT_IDNOTEXIST: device not exist
        '''
        
        # check input 
        if self.__checkCurTask():
            raise VFOSERR("have task running",VFOSERR.ERR_CON_STATUS_BUSY)
        
        if not "task_uuid" in task_option or not task_option["task_uuid"]:
            task_uuid = str(uuid4())
        else:
            task_uuid = task_option["task_uuid"]
                
        if self.task_list.has_key(task_uuid):
            raise VFOSERR("Task id exist",VFOSERR.ERR_INPUT_IDEXIST)
        
		#Default dev_id is sda2
        #task_option["dev_id"]=CloudRainbowPub.getdisktype()+"2"
        if task_option["dev_id"] == "":
            task_option["dev_id"]=CloudRainbowPub.getdisktype()+"2"	
	
        print '=========',task_option["dev_id"]
       
        if not self.__checkDevice(task_option["dev_id"]):
            raise VFOSERR("Device [%s] not exist" % task_option["dev_id"],VFOSERR.ERR_INPUT_IDNOTEXIST)
        
        #dev_size = self.__getDeviceSize(task_option["dev_id"])
        dev_size = self.__getDeviceSize(task_option["dev_id"])
        if long(task_option["img_info"]["img_size"])>dev_size:
            raise VFOSERR("Device size not too small",VFOSERR.ERR_INPUT)
        
        # register new task
        self.task_list[task_uuid] = copy.deepcopy(self.schema["schema_task_info"])
        self.task_list[task_uuid].update({
            "task_uuid":task_uuid,
            "task_key":str(uuid4()),
            "task_type":"Install_Image",
            "status":STATUS_NOTSTART,
            "result":RESULT_NONE,
            "task_option":task_option,
            "task_progress":copy.deepcopy(self.schema["schema_progress_info"])            
            })
        self.current_task_uuid = task_uuid
            
#        if kwargs.has_key("callback"):
#            callback = kwargs["callback"]
#        else:
#            callback = None
        # create a thread to finished the job
        self.curtaskthread = threading.Thread(target=self.__installImageThread,args=(task_uuid,task_option),kwargs=kwargs)
        self.curtaskthread.setDaemon(True)
        self.curtaskthread.start()
        
        ret = {'result':0,'message':"starting!","return":task_uuid}
        return ret["return"]

    def __installImageThread(self,task_uuid,task_option,**kwargs):
        '''
        
        @param task_uuid: task uuid
        @type task_uuid: schema_uuid
        @param task_option:  
                task_option:{
                    "img_info":{
                        "img_url":"",
                        "img_md5":"",
                        "img_size":"",
                        "img_type":"",
                        "img_patch_url":""
                    },
                    "dev_id":"hda",
                    "task_uuid":""
                }
        @type task_option: schema_install_option 
        '''

        # start task in background
        try:
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script
            if "img_type" in task_option["img_info"] and task_option["img_info"]["img_type"] == "ntfsfull":
                script = "ntfs_restore.srv.sh"
            else:    
                script = "disk_restore.srv.sh"
            
            shargv = [self.conf['shellscriptpath']+"/"+script,
                    "-t 1",
                    task_uuid,
                    task_option["img_info"]["img_url"],
                    "/dev/"+task_option["dev_id"],
                    task_option["img_info"]['img_size'],
                    task_option["img_info"]['img_md5'],
                    task_option["img_info"]['img_patch_url'],
                    task_option["patch_info"]["img_patch_name"],
                    task_option["patch_info"]["img_patch_md5"],
                    task_option["patch_info"]["img_patch_size"],
                ]
            
            self.syslogger.debug('installimage(%s)'," ".join(shargv))
            
            f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())
            
            # if the target is the harddisk, try to save the id and configuration to the disk.
            if not task_option["dev_id"][-1].isdigit():
                shargv = [self.conf['shellscriptpath']+"/confsave.sh"]
                f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
                f.wait()
            
            # update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS
            
        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL
            
#            if self.config["debug"]:
#                traceback.print_exc(open(self.configure["logging"]["system_log"],"a"))
#            else:
#                logging.error("error:"+str(e))
#                
            self.syslogger.error(str(e))
        if kwargs.has_key("callback"):
            callback = kwargs["callback"]
            if callable(callback):
                callback(task_uuid,self.getTaskInfo(task_uuid))
        
                
    def createImage(self,task_option,**kwargs):
        '''
        upload the disk to ftp server, as the task should take a long time, 
        so the task would run in background and return a task uuid.
        @param task_option:{
            "ftp_info":{
                "host":"",
                "username":"",
                "password":""
            },
            "dev_id":"hda",
            "task_uuid":"",
            "img_type":"",
            "img_name":"",
            "meta":""
        }
        '''
        if self.__checkCurTask():
            raise VFOSERR("have task running",VFOSERR.ERR_BUSY)
        
        if not "task_uuid" in task_option or not task_option["task_uuid"]:
            task_uuid = str(uuid4())
        else:
            task_uuid = task_option["task_uuid"]

        if self.task_list.has_key(task_uuid):
            raise VFOSERR("task id exist",VFOSERR.ERR_INPUT_IDEXIST)
        
        if not self.__checkDevice(task_option["dev_id"]):
            raise VFOSERR("device [%s] not exist" % task_option["dev_id"],VFOSERR.ERR_INPUT_IDNOTEXIST)
            
        self.task_list[task_uuid] = copy.deepcopy(self.schema["schema_task_info"])
        self.task_list[task_uuid].update({
            "task_uuid":task_uuid,
            "task_key":str(uuid4()),
            "task_type":"Create_Image",
            "status":STATUS_NOTSTART,
            "result":RESULT_NONE,
            "task_option":task_option,
            "task_progress":copy.deepcopy(self.schema["schema_progress_info"])            
            })
        self.current_task_uuid = task_uuid
        
        templatebased=True if task_option['templatebased']=='' else False
        #'YES' if task_option['meta']['type']['is_basic']=='1' else 'NO'
        task_option["tpl_name"]=task_uuid
        #task_option['templatebased']="base"
        #task_option['templatebased']=templatebased
        task_option["img_name"]="partition2.img"
        task_option["md5log"]="YES"


        #1. create a thread to finished the job
        if templatebased:
            self.curtaskthread = threading.Thread(target=self.__createImageThread,args=(task_uuid,task_option),kwargs=kwargs)
        else:
            self.curtaskthread = threading.Thread(target=self.__createImagePatchThread,args=(task_uuid,task_option),kwargs=kwargs)			
        self.curtaskthread.setDaemon(True)
        self.curtaskthread.start()
       
        ret = {'result':0,'return':task_uuid,'message':"starting!"}
        return ret["return"]

    def __createImagePatchThread(self,task_uuid,task_option,**kwargs):
        '''
        a thread to create the image
        @param task_uuid: 
        @param lib_option: lib_option = {"user_name":"","user_password":"","host_ip":""} 
        @param tpl_option:
        '''
        
        try:
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script
            if "img_type" in task_option and task_option["img_type"] == "ntfsfull":
                script = "ntfs_backup.srv.sh"
            else:   
                #tony modify, if have template based, this operator is to make patch
                script = "disk_backup.srv.sh"                    
            
            shargv = [self.conf['shellscriptpath']+"/"+script,
                "-u",task_option["ftp_info"]['username'],
                "-p",task_option["ftp_info"]['password'],
                task_uuid,
                task_option["ftp_info"]['host'],
                task_option["tpl_name"],             #template name
                task_option["dev_id"],               #dev id
                task_option["img_name"],             #image name
                task_option['md5log'],
                task_option['templatebased']]
            
            #1.upload image
            print "1.upload image"
            self.syslogger.debug('upload image(%s)'," ".join(shargv))
            
            f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            self.syslogger.info("%s upload image finished, return code is %d" % (task_uuid,f.returncode))
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())

            #2. change the meta for md5 and size ,md5=/var/task_uuid.md5 , size=/var/task_uuid.size
            #   change uuid
            print "2.change the meta's md5 and size"
            md5Path="/var/"+task_uuid+".md5"
            if not os.path.isfile(md5Path):
                print "md5 file is not foud"

            file_handler = file(md5Path,'r')
            md5=file_handler.read().strip()
            file_handler.close()
            print "the md5:",md5
   
            sizePath="/var/"+task_uuid+".size"
            if not os.path.isfile(sizePath):
                print "md5 file is not foud"
            file_handler = file(sizePath,'r')
            disk_size=file_handler.read().strip()
            file_handler.close()
            print "the size:",disk_size
     
            #5. update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS

        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL
                        
        if kwargs.has_key("callback"):
            callback = kwargs["callback"]
            if callable(callback):
                callback(task_uuid,self.getTaskInfo(task_uuid))
        print "###########", cur_task["result"]
		
    def __createImageThread(self,task_uuid,task_option,**kwargs):
        '''
        a thread to create the image
        @param task_uuid: 
        @param lib_option: lib_option = {"user_name":"","user_password":"","host_ip":""} 
        @param tpl_option:
        '''
        
        try:
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script
            if "img_type" in task_option and task_option["img_type"] == "ntfsfull":
                script = "ntfs_backup.srv.sh"
            else:   
                #tony modify, if have template based, this operator is to make patch
                script = "disk_backup.srv.sh"                    
            
            shargv = [self.conf['shellscriptpath']+"/"+script,
                "-u",task_option["ftp_info"]['username'],
                "-p",task_option["ftp_info"]['password'],
                task_uuid,
                task_option["ftp_info"]['host'],
                task_option["tpl_name"],             #template name
                task_option["dev_id"],               #dev id
                task_option["img_name"],             #image name
                task_option['md5log'],
                task_option['templatebased']]
            
            #1.upload image
            print "1.upload image"
            self.syslogger.debug('upload image(%s)'," ".join(shargv))
            
            f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            self.syslogger.info("%s upload image finished, return code is %d" % (task_uuid,f.returncode))
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())

            #2. change the meta for md5 and size ,md5=/var/task_uuid.md5 , size=/var/task_uuid.size
            #   change uuid
            print "2.change the meta's md5 and size"
            md5Path="/var/"+task_uuid+".md5"
            if not os.path.isfile(md5Path):
                print "md5 file is not foud"

            file_handler = file(md5Path,'r')
            md5=file_handler.read().strip()
            file_handler.close()
            print "the md5:",md5
   
            sizePath="/var/"+task_uuid+".size"
            if not os.path.isfile(sizePath):
                print "md5 file is not foud"
            file_handler = file(sizePath,'r')
            disk_size=file_handler.read().strip()
            file_handler.close()
            print "the size:",disk_size

			#3. put the patch to ftp
            print "3.upload patch"
            task_option["img_name"]=md5
            
            script = "put_ftp_patch.sh"                    
            shargv = [self.conf['shellscriptpath']+"/"+script,
                "-u",task_option["ftp_info"]['username'],
                "-p",task_option["ftp_info"]['password'],
                task_uuid,
                task_option["ftp_info"]['host'],
                task_option["img_name"],
                task_option['dev_id'],
                task_option['dev_id'],
                task_option['md5log'],
                task_option['templatebased']]
            
            self.syslogger.debug('upload patch(%s)'," ".join(shargv))
            
            f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            self.syslogger.info("%s upload patch finished, return code is %d" % (task_uuid,f.returncode))
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())

            self.getFtpInfo(task_option)
			#write meta data
            _dict=task_option["meta"]
            _dict["uuid"]=str(task_uuid)
            _dict["image"]["md5"]=str(md5)
            _dict["hw_requirment"]["disk_size"]=str(disk_size)
    
            metaPath="/var/"+task_uuid+".meta"
            file_handler = file(metaPath,'w') 
            file_handler.write(json.write(_dict,True))
            file_handler.close()
			
            #4. put the meta to ftp
            print "4.upload meta"
            
            script = "put_ftp_meta.sh"                    
            shargv = [self.conf['shellscriptpath']+"/"+script,
                "-u",task_option["ftp_info"]['username'],
                "-p",task_option["ftp_info"]['password'],
                task_uuid,
                task_option["ftp_info"]['host'],
                task_option["img_name"],
                task_option['dev_id'],
                task_option['dev_id'],
                task_option['md5log'],
                task_option['templatebased']]
            
            self.syslogger.debug('upload meta(%s)'," ".join(shargv))
            
            f = subprocess.Popen(shargv,cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            self.syslogger.info("%s upload meta finished, return code is %d" % (task_uuid,f.returncode))
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())
     
            #5. update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS

        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL
                        
        if kwargs.has_key("callback"):
            callback = kwargs["callback"]
            if callable(callback):
                callback(task_uuid,self.getTaskInfo(task_uuid))
        print "###########", cur_task["result"]

    def getFtpInfo(self,task_option):
        '''
        '''
        
        ftpinfo = {"host":task_option["ftp_info"]["host"],
                       "username":task_option["ftp_info"]["username"],
                       "password":task_option["ftp_info"]["password"],
                       "port":21,
                       "folder":"cloudimage/" + task_option["img_name"],
					   "file":task_option["meta"]["image"]["file"],
                       "patch_file":task_option["meta"]["image"]["patch_file"]}
        
        if len(task_option["ftp_info"]["host"].split(":")) == 2:
            ftpinfo["port"] = task_option["ftp_info"]["host"].split(":")[1]
        else:
            ftpinfo["port"] = 21

        def _ftplogin(cobj,ftpinfo):
            try:
                cobj.connect(ftpinfo["host"],ftpinfo["port"])
                cobj.login(ftpinfo["username"],ftpinfo["password"])
			    #self.cobj.cwd(self.path)
                return True
            except Exception,ftperr:
			    #self.syslogger.error("login error"+str(ftperr))
                return False

        ftp = FTP() 
        print "begin ftp login"
		
        if not _ftplogin(ftp, ftpinfo):
            print "ftp login fail."
            ftp.quit()
        else:
            print "ftp login success."
            _file_size = ftp.size(ftpinfo["folder"] + "/" + ftpinfo["file"])
            _patch_file_size = ftp.size(ftpinfo["folder"] + "/" + ftpinfo["patch_file"])
            task_option["meta"]["image"]["file_size"] = str(_file_size)
            task_option["meta"]["image"]["patch_file_size"] = str(_patch_file_size)
            ftp.quit()
                
    def getTaskInfo(self,task_uuid):
        '''
        return the task info, including the progress and result. if the task_uuid is empty, then return the current task info
        @param task_uuid:
        @type task_uuid:
        @rtype: {
            "progress":20,
            "message":"",
            "logging":"",
            "result":0
        }
        '''
        ret = copy.deepcopy(self.schema["schema_ret"])
        # get task uuid
        if task_uuid == "":
            if not self.current_task_uuid:
                ret.update({"result":0,"return":"","message":"No task running"})
                return ret["return"]
            else:
                task_uuid = self.current_task_uuid

        if not self.task_list.has_key(task_uuid):
            raise VFOSERR("Task id not exist.",VFOSERR.ERR_INPUT_IDNOTEXIST)
        
        if not self.task_list[task_uuid]["task_progress"]["result"] == RESULT_SUCCESS:
            self.__syncTaskProgress(task_uuid)
        #ret.update({"result":0,"return":self.task_list[task_uuid]["task_progress"],"message":"-"})
        #lanve edit for result
        ret.update({"result":0,"return":self.task_list[task_uuid]["task_progress"],"message":self.task_list[task_uuid]["task_progress"]["message"]})
        print self.task_list[task_uuid]["task_progress"]
#        if self.task_list[task_uuid]["task_progress"]["result"] == RESULT_SUCCESS:
#            ret.update({"result":0,"return":self.task_list[task_uuid]["task_progress"],"message":self.task_list[task_uuid]["task_progress"]["message"]})
#        else:
#            ret.update({"result":1,"return":self.task_list[task_uuid]["task_progress"],"message":self.task_list[task_uuid]["task_progress"]["message"]})

        return ret
                
        
    def __checkFtp(self,ftp_info):
        '''
        try to connected to the ftp server, and check if the ftp infomation is right.
        @return: True if connected, elsewise
        '''
    def __checkCurTask(self):
        '''
        check if there is task running.
        @return: True if has running task or else False.
        @rtype: bool         
        '''
        # if there is running thread, then return its status
        if hasattr(self,"curtaskthread"):
            return self.curtaskthread.isAlive()
        else:
            return False
        
        # check if current task pid exist, note: the pid file is set by shell script 
        pidfile = os.path.join(self.conf["taskinfopath"],"curtask","pid")
        if not os.path.isfile(pidfile):
            return False
            
        pid = getFileValue(pidfile)
        if os.path.exists("/proc/"+pid.strip()):
            return True
        else:
            return False
        
    def __syncTaskProgress(self,task_uuid):
        '''
        @rtype: schema_progress_info
        @return: schema_progress_info = {
            "status":TASK_STATUS,
            "result":RESULT_NONE,
            "progress":20,
            "message":"time elapse: 101 second",
            "debugmessage":""
        }
        '''
        try:
            if not self.task_list.has_key(task_uuid):
                raise VFOSERR("Task id not exist.",VFOSERR.ERR_IDNOTEXIST)
            

            progress = self.task_list[task_uuid]["task_progress"]

            taskinfo_path = os.path.join(self.conf["historytaskpath"],task_uuid)
            progressfile  = os.path.join(taskinfo_path,"progress")
            resultfile    = os.path.join(taskinfo_path,"result")
            messagefile   = os.path.join(taskinfo_path,"message")
            statusfile    = os.path.join(taskinfo_path,"status")
            debugfile     = os.path.join(taskinfo_path,"logfile")
            #self.syslogger.debug(progressfile)
            
            
            progress.update({
                "result":getFileValue(resultfile),
                "status":getFileValue(statusfile),
                "message":getFileValue(messagefile),
                "debug_message":getFileValue(debugfile),
                "progress":0
                })
                
            #self.syslogger.debug(" task info is %s " % str(progress))
            # adapt
            if not progress["status"]:
                progress["status"] = STATUS_NOTSTART
                progress["result"] = RESULT_NONE
            elif progress["status"] == STATUS_END:
                progress["progress"] = 100
#                progress['message'] = "task ended"               
            elif progress["status"] == STATUS_BUSY:
                if os.path.exists(progressfile):
                    fp = os.popen("tail -1 " + progressfile )
                    fcontent = fp.read()
                    if fcontent :
                        arr = fcontent.split()
                        progress['message'] += ":"+fcontent
                        if "%" in arr[0]:
                            progress['progress'] = int(float(arr[0][0:-1]))
                        elif arr[0] == "100" :
                            progress['progress'] = 100
                    fp.close();
                else:
                    progress['progress'] = 0
            else:
                progress['result'] = RESULT_UNKNOW
                progress['message'] = "unknow status!"
                
            if (0 == (progress['progress'] % 10)):
                self.syslogger.debug("Task progress:"+str(progress['progress']))
            
            return progress
        except Exception,e:
            self.syslogger.debug(str(e))
        
    def saveGuestOSConf(self,tplconfig,**kwargs):
        '''
        binding with osconfsave.sh
        '''
        try:
            # save to ramdisk with special format
            fd = open(self.conf["guestosconfpath"],"w")
            kvconf = []
            for k,v in tplconfig.iteritems():
                for k2,v2 in v.iteritems():
                    kvconf.append("%s=%s\n"%(k2.lower(),str(v2)))
                
            fd.writelines(kvconf)
            fd.close()
            
            # call script and save to disk
            saveconf_script = os.path.join(self.conf["shellscriptpath"],"osconfsave.sh")
            sh = ["bash",saveconf_script,CloudRainbowPub.getdisktype()+"2"]
            #ret = rawExec([saveconf_script])
            ret = rawExec(sh)
            return ret
        except Exception,e:
            return {"result":100,"return":"","message":"save configure error: %s" % str(e)}
    
    def saveGuestAppConf(self, appconf, **kwargs):
        try:
            fd = open(self.conf["guestosconfpath"],"w")
            print(appconf)
            p.dump(appconf,fd)
            fd.close()       
        
            # call script and save to disk
            saveconf_script = os.path.join(self.conf["shellscriptpath"],"osconfsave.sh")
            sh = ["bash",saveconf_script,CloudRainbowPub.getdisktype()+"2"]
            #ret = rawExec([saveconf_script])
            ret = rawExec(sh)
            return ret            
        except Exception,e:
            return {"result":100,"return":"","message":"save configure error: %s" % str(e)}
    
    def reboot(self,task_option,**kwargs):
        '''
        
        '''
        # check input 
        if self.__checkCurTask():
            raise VFOSERR("have task running",VFOSERR.ERR_CON_STATUS_BUSY)
        
        if not "task_uuid" in task_option or not task_option["task_uuid"]:
            task_uuid = str(uuid4())
        else:
            task_uuid = task_option["task_uuid"]
                
        if self.task_list.has_key(task_uuid):
            raise VFOSERR("Task id exist",VFOSERR.ERR_INPUT_IDEXIST)
               
        
        # register new task
        self.task_list[task_uuid] = copy.deepcopy(self.schema["schema_task_info"])
        self.task_list[task_uuid].update({
            "task_uuid":task_uuid,
            "task_key":str(uuid4()),
            "task_type":"reboot",
            "status":STATUS_NOTSTART,
            "result":RESULT_NONE,
            "task_option":task_option,
            "task_progress":copy.deepcopy(self.schema["schema_progress_info"])            
            })
        self.current_task_uuid = task_uuid

        self.curtaskthread = threading.Thread(target=self.__reboot,args=(task_uuid,task_option),kwargs=kwargs)
        self.curtaskthread.setDaemon(True)
        self.curtaskthread.start()
        
        ret = {'result':0,'message':"starting!","return":task_uuid}
        return ret["return"]
        
    def __reboot(self,task_uuid,task_option,**kwargs):
        '''      
       
        '''
        # start task in background
        try:
            ret = {"result":0,"return":"","message":"done"}
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script
                        
            reboot_script = os.path.join(self.conf["shellscriptpath"],"reboot.sh")
            
            f = subprocess.Popen([reboot_script],cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())
                      
            # update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS
            
        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL            
#          
            self.syslogger.error(str(e))
            ret = {"result":102,"return":"","message":str(e)}  
        
     
    def __shutdown(self,task_uuid,task_option,**kwargs):
        '''      
       
        '''
        # start task in background
        try:
            ret = {"result":0,"return":"","message":"done"}
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script
                        
            reboot_script = os.path.join(self.conf["shellscriptpath"],"shutdown.sh")
            
            f = subprocess.Popen([reboot_script],cwd=self.conf['shellscriptpath'],stderr=subprocess.PIPE)
            f.wait()
            
            if f.returncode != 0:
                raise Exception(f.stderr.read())
                      
            # update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS
            
        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL            
#          
            self.syslogger.error(str(e))
            ret = {"result":103,"return":"","message":str(e)}
       
    def __resetDisk(self,task_uuid,task_option,**kwargs):
        '''      
        
        '''
        # start task in background
        try:
            
            cur_task = self.task_list[task_uuid]
            cur_task["status"] = STATUS_BUSY
            
            # run script                        
            task_option = []
            
            #transform the string to list, then fill the task_option
            disklist = CloudRainbowPub.getdisklist()
            diskIndex = 0
            while ('' != disklist[diskIndex]):
                if 0 == diskIndex:
                    task_option.append({"name":disklist[diskIndex],"type":"sys"})
                else:
                    task_option.append({"name":disklist[diskIndex],"type":"other"})
                diskIndex = diskIndex+1 
                
            resetdisk_script = os.path.join(self.conf["shellscriptpath"],"resetdisk.sh")
            for diskinfo in task_option:
                ret = rawExec(["bash",resetdisk_script,diskinfo["name"],diskinfo["type"]])
                if ret['result'] != 0:
                    break
              
            if ret['result'] == 0: 
                ret['message']= "done."
            else:
                ret['message']= "fail."    
                
            if kwargs.has_key("callback"):
                    callback = kwargs["callback"]
                    if callable(callback):
                        callback("",ret)
                            
            if ret['result'] == 0:                
                sd_script = os.path.join(self.conf["shellscriptpath"],"shutdown.sh")
                ret = rawExec([sd_script])            
            
                      
            # update task info
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_SUCCESS
            
        except Exception,e:
            cur_task["status"] = STATUS_END
            cur_task["result"] = RESULT_FAIL            
#          
            self.syslogger.error(str(e))
            ret = {"result":104,"return":"","message":str(e)}  
                      
    def resetDisk(self,task_option,**kwargs):
        '''
        
        '''
        # check input 
        if self.__checkCurTask():
            raise VFOSERR("have task running",VFOSERR.ERR_CON_STATUS_BUSY)
        
        if not "task_uuid" in task_option or not task_option["task_uuid"]:
            task_uuid = str(uuid4())
        else:
            task_uuid = task_option["task_uuid"]
                
        if self.task_list.has_key(task_uuid):
            raise VFOSERR("Task id exist",VFOSERR.ERR_INPUT_IDEXIST)
               
        
        # register new task
        self.task_list[task_uuid] = copy.deepcopy(self.schema["schema_task_info"])
        self.task_list[task_uuid].update({
            "task_uuid":task_uuid,
            "task_key":str(uuid4()),
            "task_type":"resetDisk",
            "status":STATUS_NOTSTART,
            "result":RESULT_NONE,
            "task_option":task_option,
            "task_progress":copy.deepcopy(self.schema["schema_progress_info"])            
            })
        self.current_task_uuid = task_uuid

        self.curtaskthread = threading.Thread(target=self.__resetDisk,args=(task_uuid,task_option),kwargs=kwargs)
        self.curtaskthread.setDaemon(True)
        self.curtaskthread.start()
        
        ret = {'result':0,'message':"starting!","return":task_uuid}
        return ret["return"]

    def shutdown(self,task_option,**kwargs):
        '''
        
        '''
        # check input 
        if self.__checkCurTask():
            raise VFOSERR("have task running",VFOSERR.ERR_CON_STATUS_BUSY)
        
        if not "task_uuid" in task_option or not task_option["task_uuid"]:
            task_uuid = str(uuid4())
        else:
            task_uuid = task_option["task_uuid"]
                
        if self.task_list.has_key(task_uuid):
            raise VFOSERR("Task id exist",VFOSERR.ERR_INPUT_IDEXIST)
               
        
        # register new task
        self.task_list[task_uuid] = copy.deepcopy(self.schema["schema_task_info"])
        self.task_list[task_uuid].update({
            "task_uuid":task_uuid,
            "task_key":str(uuid4()),
            "task_type":"shutdown",
            "status":STATUS_NOTSTART,
            "result":RESULT_NONE,
            "task_option":task_option,
            "task_progress":copy.deepcopy(self.schema["schema_progress_info"])            
            })
        self.current_task_uuid = task_uuid

        self.curtaskthread = threading.Thread(target=self.__shutdown,args=(task_uuid,task_option),kwargs=kwargs)
        self.curtaskthread.setDaemon(True)
        self.curtaskthread.start()
        
        ret = {'result':0,'message':"starting!","return":task_uuid}
        return ret["return"]
                                                
    def _dispatch(self,method,*args):
        '''
        for xmlrpc use
        '''
        try:
            if method.startswith("_"):
                raise VFOSERR("unsupported message",VFOSERR.ERR_CON_ACL)
            func = getattr(self,method)
            return {"return":func(*args),"result":0,"message":"done"}
        except VFOSERR,ee:
            return {"return":"","result":ee.errid,"message":ee}
        except Exception,e:
            return {"return":"","result":VFOSERR.ERR_UNEXPECTED,"message":e}
    
if __name__ == "__main__":
    from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler,SimpleXMLRPCServer
    configure = {
        # file
        "configure_file":"/etc/vfos.basic.server.conf",
        # runtime folders

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
        'cgipath':'/var/www/lighttpd/cgi',
        'htmlpath':'/var/www/lighttpd/html',
        # binding with shell script: osconfsave.sh
        'guestosconfpath':"/var/guestos.conf",

        # envconf
        'vmidfile':'/tmp/cfg/vmid',
        'boothostfile':'/tmp/cfg/boothost',
        'debuglogfile':'/tmp/websrv.log',
        
        # network
        'ip':"0.0.0.0",
        "port":7878
        }

    instance = CloudRainbowAgent(configure)
    server = SimpleXMLRPCServer(('0.0.0.0', configure["port"]))
    server.RequestHandlerClass.rpc_paths = ()
    server.register_instance(instance)    
    server.serve_forever()
    
    
