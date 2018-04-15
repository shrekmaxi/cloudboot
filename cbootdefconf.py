#import pickle

cboot_config={
# register information from the url 
"domain_mgr_url":"",
"domain":"",
"confbox_url":"",
"confbox_uuid":"",
"rpcbox_url":"",
"rpcbox_uuid":"",
"vm_ip":"",
"vm_mac":"",
"vm_description":"",
"vm_uuid":""}

'''
fd = open("./cloudrainbow.conf","w")
pickle.dump(cboot_config, fd)
fd.close()

fd = open("./cloudrainbow.conf","r")
test = pickle.load(fd)
fd.close()
'''