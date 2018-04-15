# -*- coding: utf-8 -*-
'''
Created on 2011-1-4
## Copyright (C) 2007-2010 The PowerallNetworks
## See LICENSE for details
##----------------------------------------------------------------------
'''
class VFOSERR(Exception):
    '''
    defined the exception of the cloud rainbow module for defended programming.
    1)Input error including format error and consistent error. 
        [110-129] Format error : 
            The input format is not expected. 
        [130-149] Consistent error: 
            Means the caller expected some state, but it isn't. Mostly for state recorded system.
    2)Condition error (200-299): the function expected some condition. if the condition not ready, then raise error.
        ### System condition ###
        [210-219] Filesystem:File operation error
        [220-229] Database:Database operation error
        [230-239] Network:Network connection error
        [240-249] IO: IO error
        [250-259] Memory: 
        ### Logical condition ###
        [260-269] Privileged:
        [270-279] Status: busy, locked
    2)Runtime error (300-399): the status change during runtime, especially for IO (filesystem/DB/network), memory.
        [310-319] Filesystem:File operation error
        [320-329] Database:Database operation error
        [330-339] Network:Network connection error
        [340-349] IO: IO error
        [350-359] Memory: 
    3)Environment error (400-499): for the module/system initiation, the environment not ready, especially for initiate.
        [410-419] Filesystem:File operation error
        [420-429] Database:Database operation error
        [430-439] Network:Network connection error
        [440-449] IO: IO error
        [450-459] Memory: 
    4)Logical error (500-599): especially for programming
        
    5)Unexpected error (600): 
        
    '''
    ERR_INPUT         = 100
    ERR_INPUT_FORMAT= 110
    ERR_INPUT_CONSISTANCE = 130
    ERR_INPUT_IDNOTEXIST = 131
    ERR_IDNOTEXIST = 131
    ERR_INPUT_IDEXIST = 132
    
    ERR_CONDITION     = 200
    ERR_CON_FS         = 210
    ERR_CON_FS_NOTEXIST = 211
    ERR_CON_DB         = 220
    ERR_CON_NET     = 230
    ERR_CON_IO         = 240
    ERR_CON_MEM        = 250
    ERR_CON_ACL     = 260
    ERR_CON_STATUS     = 270
    ERR_CON_STATUS_BUSY     = 271
    ERR_BUSY = 271
    
    ERR_RUNTIME     = 300
    ERR_RUN_FS         = 310
    ERR_RUN_DB         = 320
    ERR_RUN_NET     = 330
    ERR_RUN_IO         = 340
    ERR_RUN_MEM        = 350
    
    ERR_ENVIRONMENT    = 400
    ERR_ENV_FS         = 410
    ERR_ENV_FS_NOTEXIST = 411
    ERR_ENV_DB         = 420
    ERR_ENV_NET     = 430
    ERR_ENV_IO         = 440
    ERR_ENV_MEM        = 450
    
    ERR_LOGICAL        = 500
    
    ERR_UNEXPECTED    = 600
    
    def __init__(self,message="",errid=1):
        super(VFOSERR,self).__init__(message)
        self.message = message
        self.errid = errid
    def __str__(self):
        return repr(self.message)

