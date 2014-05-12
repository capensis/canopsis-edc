#!/usr/bin/env python
#--------------------------------
# copyright (c) 2011 "capensis" [http://www.capensis.com]
#
# this file is part of canopsis.
#
# canopsis is free software: you can redistribute it and/or modify
# it under the terms of the gnu affero general public license as published by
# the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# canopsis is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the
# gnu affero general public license for more details.
#
# you should have received a copy of the gnu affero general public license
# along with canopsis.  if not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

#################################################
#						#
#
# or how to return datas from multipe sources	#
# in order to register them through one format	#
#						#
#################################################
from datetime import datetime
import sys
import os

global base
base = os.environ['EDC_HOME']
global log_dir
log_dir = os.environ['EDC_LOG'] 

#------------------------------------------------
# ---- Import de la biblog
#------------------------------------------------

#import settings
from connector import biblog
from connector.biblog import loadMsgConf

os.environ["BIB_LOGCONF_PATH"]= "%s/cfg/ref/log.json" % base
os.environ["BIB_MSG_CONFPATH"]= "%s/cfg/ref/msg.conf" % base

class Message:
        def __init__(self, logfile, debug=False):
                try:
                        _logconf = loadMsgConf( os.environ["BIB_LOGCONF_PATH"] )
                        _msgconf = loadMsgConf( os.environ["BIB_MSG_CONFPATH"] )
                        self.logging = biblog.BibLogger( _logconf, _msgconf)
                except Exception,e:
                        print ("ERROR : Error while log initialisation : "+str(e))
                        sys.exit(4)
                self.logfile = logfile +"log-"+datetime.now().strftime("%Y%m%d")
                self.errors  = []
                self.messages= []
                self.debug   = debug

        def addError(self, errorCode,  *params):
                level = 2
                error = { 'code': errorCode }
                if level == 1:
                        self.logging.log( errorCode )
                        os._exit()
                else:
                        self.logging.log( errorCode, params )

        def addMessage(self, msgCode, *params) :
                message =       { 'content' : msgCode }
                if len ( sys.argv ) > 2 and '-d' in sys.argv:
                        self.messages.append( message )
                        self.logging.log( msgCode, *params )
                elif self.debug:
                        self.messages.append( message )
                        self.logging.log( msgCode, *params )


