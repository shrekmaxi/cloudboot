import os , sys
import lib_json 

class TSStorageMeta:
    _dict={}

    def ReadMeta(self):
        metaPath="/var/meta"
        if not os.path.isfile(metaPath):
            print "file of not found metaPath"
            return {}

        file_handler = file(metaPath,'r') 
        self._dict = lib_json.read(file_handler.read().strip()) 
        file_handler.close()
        return self._dict 
        

    def WriteMeta(self,hashID):
        file_handler = file(metaPath+"_1",'w') 
        file_handler.write(lib_json.write(self._dict,True));       
        file_handler.close()

    def SetMetaValue(self,type,key,value):
        try:
            m_dict = {}
            if self._dict.has_key(type) :
                m_dict = self._dict[type]
                m_dict[key] = value
            else :
                m_dict = {key:value}
                self._dict[type] = m_dict;
        except:
            print sys.exc_info()
            return False
        
        return True

    def SetMeta(self,type,value):
        try:
            self._dict[type] = value
        except:
            return False

        return True



    def GetMetaValue(self,type,key):
        try:
            m_dict = {}
            value  = ""
            m_dict = self._dict[type]
            value  = m_dict[key]
        except:
            return ""
        print value
        return value


    def GetMeta(self,type):
        try:
            m_dict = {}
            m_dict = self._dict[type]
        except:
            return {}
        
        print m_dict
        return m_dict


if __name__ == '__main__':
#    meta = TSStorageMeta()
#    meta.ReadMeta()
#    print meta._dict
#    print meta.GetMeta("appconfig_info")
    print "script name:", sys.argv[0] 

    for i in range(1, len(sys.argv)): 
        print "arg", i, sys.argv[i] 


#   _dict={}
    _dict=lib_json.read(sys.argv[1])
    key=sys.argv[2]
   
    if _dict.has_key(key):
        print _dict[key]

