import os
import subprocess

def getdisktype():
    #shstring = ["fdisk -l| grep 'Disk /dev/.*d.'|awk '{print $2}'|cut -c 6-8 | head -1"]    
    #shstring = ["fdisk -l 2>/dev/null| grep 'Disk /dev/[a-z]\{1,2\}d.'|awk '{print $2}'|cut -c 6-|cut -d: -f1"]    
    shstring = ["fdisk -l 2>/dev/null| grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|head -1|awk '{print $2}'|cut -c 6-|cut -d: -f1"]    
    f = subprocess.Popen(shstring,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
    ret = f.stdout.read().strip('\n')
    return ret

    #if (os.system("fdisk -l | grep 'Disk /dev/sda'") == 0):
    #    return "sda"

    #if (os.system("fdisk -l | grep 'Disk /dev/hda'") == 0):
    #    return "hda"

    #if (os.system("fdisk -l | grep 'Disk /dev/xvda'") == 0):
    #    return "xvda"
    

def getdisklist():
    #shstring = ["fdisk -l| grep 'Disk /dev/.*d.'|awk '{print $2}'|cut -c 6-8 | head -1"]    
    #shstring = ["fdisk -l 2>/dev/null| grep 'Disk /dev/[a-z]\{1,2\}d.'|awk '{print $2}'|cut -c 6-|cut -d: -f1"]    
    shstring = ["fdisk -l 2>/dev/null| grep 'Disk /dev/[a-z]\{1,2\}d.'|sort|awk '{print $2}'|cut -c 6-|cut -d: -f1"]    
    f = subprocess.Popen(shstring,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
    ret = f.stdout.read()
    disklist = ret.split('\n')
    return disklist
    
if __name__ == "__main__":
    print getdisklist()
