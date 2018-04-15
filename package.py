import compileall
import os
import sys

path=r'D:\lighttpd\source'
dstpath=r'D:\lighttpd'

compileall.compile_dir(path)
files = os.listdir(path)


for file in files:

    if file.split('.')[1]=='pyc':
       print file 
       if os.path.exists(os.path.join(path,file)):
           print "remove"
           os.remove(os.path.join(dstpath,file))
       os.rename(os.path.join(path,file),os.path.join(dstpath,file))
       #print (path+file,os.path.join(dstpath,file))

