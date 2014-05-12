#!python
# -*- coding: utf-8 -*-

import sys, os, types
#import plx, os
import logging, bibutils
from logging.handlers import RotatingFileHandler
from string import Template
import os, sys
import time
import errno

logging.getLogger('BibConsoleLogger')
logging.getLogger('BibInfoLogger')
logging.getLogger('BibDebugLogger')
logging.getLogger('BibErrLogger')


if not os.environ.has_key('EDC_LOG') or os.environ['EDC_LOG'] == '':
        dir_path                =       os.path.dirname(os.path.abspath(__file__))
        edc_home                =       "%s/../.." % dir_path
        os.environ['EDC_LOG']  =       "%s/log" % edc_home


"""
PUBLIC MODULE VARIABLES
"""

"""
PRIVATE ATTRIBUTES
"""
LOGFORMAT = EXPLOGFORMAT = "[%(asctime)s-%(msecs)d]%(message)s"
EXTENDEDFORMAT = "[%(PID)s][%(cdmsg)s][%(typemsg)s][%(cdlevel)s][%(cdtype)s][%(cdapp)s][%(flbc)s][%(exec_user)s][%(oksupervise)s][%(urlhelp)s][%(progpath)s][%(threadName)s][%(funcName)s][%(lineno)s]"
EXCEPTFORMAT="[%(PID)s] "
DATEFORMAT = '%m-%d %H:%M:%S',
DATEFORMAT = "%Y-%m-%d %H:%M:%S"

"""
PRIVATE FUNCTIONS
"""
def current_user():
	pass
#	try:
		#return pwd.getpwuid(os.getuid()).pw_name #NOT PORTABLE
		#return plx.get_username()
#		return "NOT_IMP"
#	except KeyError:
#		return "(unknown)"
	
def getCurrentThreadName():
	import threading
	if hasattr(threading,"current_thread"):
		athread = threading.current_thread()
		cthread = athread.name
	else:
		cthread = "<MainThread?>"
	return cthread

ginfo = {'filename':'', 'module':'', 'lineno':'', 'funcName':'','PID':'','exec_user':'','progpath':'',"threadName":''}

def _getInfo():
	fn, lno, func = _findCaller()
	filename = os.path.basename(fn)
	dirname = os.path.dirname(fn)
	module = os.path.splitext(filename)[0]
	info = {'filename':filename, 'module':module, 'lineno':str(lno), 'funcName':func,'PID':str(os.getpid()),'exec_user':current_user(),'progpath':dirname,"threadName":getCurrentThreadName()}
	for f in ginfo:
		if not ginfo[f]=='':
			info[f]=ginfo[f]
	return info

# FOR BACKWARD COMPATIBILITY CALL SIGNATURE (python 2.4 has no extra params for logging)
# Adding the 'username' and 'funcname' specifiers
# They must be attributes of the log record

# Custom log record
class OurLogRecord(logging.LogRecord):
	def __init__(self, name, level, fn, lno, msg, args, exc_info, func):
		# Don't pass all args to LogRecord constructor bc it doesn't expect "extra"
		#func not used for backward compatibility
		logging.LogRecord.__init__(self, name, level, fn, lno, msg, args, exc_info)
		# Adding format specifiers is as simple as adding attributes with
		# same name to the log record object:
		self.funcname = calling_func_name()

class OurLogger(logging.getLoggerClass()):
	def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
		# Don't pass all makeRecord args to OurLogRecord bc it doesn't expect "extra"
		rv = OurLogRecord(name, level, fn, lno, msg, args, exc_info, func)
		# Handle the new extra parameter.
		# This if block was copied from Logger.makeRecord
		if len(args)>0:
			for key in args[0]:
					if (key in ["message", "asctime"]) or (key in rv.__dict__):
						raise KeyError("Attempt to overwrite %r in LogRecord" % key)
					rv.__dict__[key] = args[0][key]
		return rv

class BibLogFormatter(logging.Formatter):
	last_s=None
	def formatTime(self, record, datefmt=None):
		ct = self.converter(record.created)
		if datefmt:
			s = time.strftime(datefmt, ct)
		else:
			t = time.strftime(DATEFORMAT, ct)
			s = "%s" % (t)
		self.last_s=s
		return s
	def formatException(self,exc_info):
		info=_getInfo()
		prefix="\t["+self.last_s+"]"+EXCEPTFORMAT%info
		exc = logging.Formatter.formatException(self,exc_info)
		exc=exc.replace("\n","\n"+prefix)
		return prefix+exc

# Register our logger
logging.setLoggerClass(OurLogger)

# Current user

# Calling Function Name
def calling_func_name():
	if not ginfo['funcName']=='':
		return ginfo['funcName']
	return calling_frame().f_code.co_name

def calling_frame():
	f = sys._getframe()

	while True:
		if is_user_source_file(f.f_code.co_filename):
			return f
		f = f.f_back

def is_user_source_file(filename):
	return os.path.normcase(filename) not in (_srcfile, logging._srcfile)

def _current_source_file():
	if __file__[-4:].lower() in ['.pyc', '.pyo']:
		return __file__[:-4] + '.py'
	else:
		return __file__

_srcfile = os.path.normcase(_current_source_file())
## end of http://code.activestate.com/recipes/474089/ }}}

def _getConsoleHandler(level,logformat):
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(level)

	# set a format which is simpler for console use
	formatter = BibLogFormatter(fmt=str(logformat))

	# tell the handler to use this format
	console.setFormatter(formatter)
	return console

class ErrorFilter(logging.Filter):
	def filter(self, rec):
		return rec.levelno == logging.INFO
	
def _bibThrow(exc_info=(None, None, None), errorMsg=''):
	"""Re-raise the latest exception given by exc_info tuple (as returned by
	sys.exc_info()) with additional errorMsg text.
	Exceptions with non-standard constructors get re-raised as derived
	exceptions, with recorded original error message and original traceback.
	Parameters:
		exc_info: (<exception class>, <exception instance>, <traceback object>)
			tuple
		errorMsg: error message text to add to the exception error message
	"""
	excClass, exc, tb = exc_info
	try:
		# re-raise original exception with added custom error message
		raise excClass( excClass("%s: %s" % (exc, errorMsg)), tb)
	except TypeError:
		if excClass == TypeError:
			# original exception is TypeError, which has a standard constructor:
			# safe to re-raise this way
			raise excClass( excClass("%s: %s" % (exc, errorMsg)), tb)

		# TypeError due to non-standard exception constructor 
		if isinstance(excClass, (types.ClassType, type)) \
		   and issubclass(excClass, Exception):
			# raise derived exception class with added custom error message
			class CustomInfoException(excClass):
				def __init__(self, info='', args=[]):
					self._info = info
					excClass.__init__(self, *args)

				def __str__(self):
					return "%s: %s" % (excClass.__str__(self), self._info)

			CustomInfoException.__name__ = excClass.__name__
			raise CustomInfoException( CustomInfoException(info=errorMsg, args=exc.args), tb)
		else:
			# raise base Exception class with added original exception
			# message plus custom error message. Safe for old string exceptions.
			raise Exception (Exception("%s: %s: %s" % (getattr(excClass, '__name__', excClass), exc or excClass, errorMsg)), tb)

def _currentframe():
	"""Return the frame object for the caller's stack frame."""
	try:
		raise Exception
	except:
		return sys.exc_info()[2].tb_frame.f_back
	
#if hasattr(sys, '_getframe'): _currentframe = lambda: sys._getframe(3)
if hasattr(sys, 'frozen'): #support for py2exe
	_srcfile = "logging%s__init__%s" % (os.sep, __file__[-4:])
elif __file__[-4:].lower() in ['.pyc', '.pyo']:
	_srcfile = __file__[:-4] + '.py'
else:
	_srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

def _callersname():
	import sys
	return sys._getframe(2).f_code.co_name

## end of http://code.activestate.com/recipes/66062/ }}}

def _findCaller():
		"""
		Find the stack frame of the caller so that we can note the source
		file name, line number and function name.
		"""
		f = _currentframe()
		#On some versions of IronPython, _currentframe() returns None if
		#IronPython isn't run with -X:Frames.
		if f is not None:
			f = f.f_back
		rv = "(unknown file)", 0, "(unknown function)"
		while hasattr(f, "f_code"):
			co = f.f_code
			filename = os.path.normcase(co.co_filename)
			if filename == _srcfile:
				f = f.f_back
				continue
			acl = co.__class__.__name__
			rv = (co.co_filename, f.f_lineno, co.co_name)
			break
		return rv

def _getExtra(msgId=None,msg=None):
	info = _getInfo()
	if msgId :
		for key in msgId:
			info[key]=msgId[key]
		logformat = LOGFORMAT
		for nm in info:		
			logformat = logformat.replace("%("+nm+")d","")
			logformat = logformat.replace("%("+nm+")s","")
		logformat = logformat.replace("%(asctime)s","")
		logformat = logformat.replace("%(threadName)s","")
		logformat = logformat.replace("%(message)s","")
		logformat = logformat.replace("%(msecs)d","")
		
	return info

"""
PUBLIC MODULE CLASSES
"""

TYPE_MSG_CONV={'E':'ERROR','D':'DEBUG','W':'WARN','I':'INFO'}
LEVELS={'DEBUG':0,'INFO':10,'ERROR':20}

def is_array(var):
	return isinstance(var, (list, tuple))

class BibMessageLog(object):
	msgstr = None
	type = None
	def __init__(self,msgIn,params=[],extendedformat=None):
		msg=None
		if not extendedformat:
			print ("PROGRAMMING ERROR, it to remind me, this will never occur in real life")
		if not is_array(params):
			params=[str(params)]
		prm = None 
		if bibutils.is_array(params):
			prm = bibutils.array2Dict(params,"P")
			prm["P0"]=current_user()
			
		if isinstance(msgIn, dict):
			msg=bibutils.dict2obj(msgIn)
		else:
			if type(msgIn) ==bibutils.dict2obj:
				msg=msgIn
		self.type = "ERROR"
		msgstr = "#UNDEF#_ID"
		if msg :
			import re
			self.type = '?'
			if msg.typemsg in TYPE_MSG_CONV:
				self.type = TYPE_MSG_CONV[msg.typemsg]
			msgstr = msg.lbc.replace("%","$")
			msgstr = re.sub(r"\$(\d)",r"$P\1",msgstr)
			try:
				self.msgstr = msgstr
				if prm:
					self.msgstr = Template(msgstr).safe_substitute(prm)
				msgIn["flbc"] = self.msgstr 
				extra=_getExtra(msgIn)
				self.msgstr =  extendedformat % extra
			except KeyError :
				err = str(sys.exc_info()[1])
				pass
			except Exception :
				err = str(sys.exc_info()[1])
				pass

	def __repr__(self): #python 3
		return str(self.msgstr).replace("%","?")

"""
PUBLIC FUNCTIONS
"""

def loadMsgConf(path):
	jsonconf = bibutils.getObjectFromJson(path)
	conf=bibutils.dict2obj(jsonconf)
	return conf

#@deprecated
def bibMsgRaise(cdmsg="", params=[]):
	_bibThrow(sys.exc_info(), cdmsg)
	
class BibException(Exception):
	pass
	
class BibBadConfException(BibException):
	pass

loggerInstNumber=0
class BibLogger(object):
	_errLogger = None
	_infoLogger = None
	_dbgLogger = None
	_consoleLogger = None
	_excLogger = None
	cfgLog = None
	msgconf = None
	instNumber=0
	maxBytes=0
	backupCount=0
	singlefile = None
	dbgfile = None
	errfile = None
	infofile = None
	logInConsole = 1
	level = 0
	logformat = ""
	extendedformat= ""
	quiet=False

	def __init__(self,confs=None,msgconf=None,logformat=LOGFORMAT,extendedformat=EXTENDEDFORMAT,quiet=False):
		global loggerInstNumber
		loggerInstNumber+=1
		self.instNumber=loggerInstNumber
		self.logformat = logformat
		self.quiet=quiet
		self.extendedformat=extendedformat
		_msgconf=msgconf
		if not msgconf:
			if "BIB_MSGCONF_PATH" in os.environ:
				BIB_MSGCONF_PATH=os.environ["BIB_MSGCONF_PATH"]
				_msgconf = loadMsgConf(BIB_MSGCONF_PATH)
			else:
				print ("#### FATAL ERROR : ###\nNo logging configuration found and missing BIB_MSGCONF_PATH environment variable")
				exit(0)
		else:
			if not isinstance(msgconf, bibutils.dict2obj):
				if isinstance(msgconf, dict):
					_msgconf=bibutils.dict2obj(msgconf)
		_confs=confs
		if not isinstance(confs, dict) :
			if "BIB_LOGCONF_PATH" in os.environ:
				BIB_LOGCONF_PATH=os.environ["BIB_LOGCONF_PATH"]
				_confs = loadMsgConf(BIB_LOGCONF_PATH)
			else:
                                print ("#### FATAL ERROR : ###\nNo logging configuration found and missing BIB_MSGCONF_PATH environment variable")
				exit(0)
		else:
			if not isinstance(confs, bibutils.dict2obj):
					_confs=bibutils.dict2obj(confs)
	
		if len ( sys.argv ) > 1:
			log_dir		=	"%s/%s" % ( os.environ['EDC_LOG'] , sys.argv[1] )
		else:
			log_dir		=	os.environ['EDC_LOG']
	
		if "singlefile" in _confs:
			if _confs["singlefile"]:
				self.singlefile = "%s/%s" % (log_dir,_confs["singlefile"])
				self.createdir(self.singlefile)
				self.dbgfile=self.singlefile
				self.errfile=self.singlefile
				self.infofile=self.singlefile
		else:
			if "multi-dbgfile" in _confs:
				if _confs["multi-dbgfile"]:
					self.dbgfile = "%s/%s" % (log_dir,_confs["multi-dbgfile"])
					self.createdir(self.dbgfile)
		
			if "multi-errfile" in _confs:
				if _confs["multi-errfile"]:
					self.errfile = "%s/%s" % (log_dir,_confs["multi-errfile"])
					self.createdir(self.errfile)

			if "multi-infofile" in _confs:
				if _confs["multi-infofile"]:
					self.infofile = "%s/%s" % (log_dir,_confs["multi-infofile"])
					self.createdir(self.infofile)
				
		if "level" in _confs:
			if _confs["level"] in LEVELS:
				if LEVELS[_confs["level"]]:
					self.level=LEVELS[_confs["level"]]
			
		if  "rotate-maxBytes" in _confs:
			if _confs["rotate-maxBytes"]:
				self.maxBytes=int(_confs["rotate-maxBytes"])

		if  "rotate-backupCount" in _confs:
			if _confs["rotate-backupCount"]:
				self.backupCount=int(_confs["rotate-backupCount"])

		if  "logInConsole" in _confs:
			if _confs.logInConsole:
				self.logInConsole=int(_confs.logInConsole)
		
		if not _msgconf :
			raise BibBadConfException("_msgconf null, Messages' file is incorrect")
		if not _msgconf :
			raise BibBadConfException("_msgconf null, Messages' file is incorrect")
		self.msgconf = _msgconf
	
		if not 'BIB_DBG_DEFAULT_MESSAGE' in self.msgconf:
			raise BibBadConfException("BIB_DBG_DEFAULT_MESSAGE not found, Messages' file is incorrect")
		self.msgconf = _msgconf
		
	def setLevel(self,level):
		if level in LEVELS:
				if LEVELS[level]:
					self.level=LEVELS[level]
		else:
			print ("Unknown trace level : "+level)
			
	def createdir(self,errfile):
			path=os.path.dirname(errfile)
			if len(path)==0:
				return
			try:
				os.makedirs(path)
			except OSError :
				etype = sys.exc_info()[0]
				
	def _getErrLogger(self):
		if self.singlefile :
			return self._getDebugLogger()
		if self._errLogger == None and self.errfile:
			self._errLogger = logging.getLogger('BibErrLogger')
			hdlr = RotatingFileHandler(self.errfile, maxBytes=self.maxBytes, backupCount=self.backupCount)
			formatter = BibLogFormatter(fmt=str(self.logformat))
			hdlr.setFormatter(formatter)
			self._errLogger.addHandler(hdlr) 
			self._errLogger.setLevel(logging.ERROR)
		return self._errLogger
	
	def _getConsoleLogger(self):
		if self._consoleLogger == None:
			self._consoleLogger = logging.getLogger('BibConsoleLogger')
			formatter = BibLogFormatter(fmt=str(self.logformat))
			self._consoleLogger.setLevel(logging.ERROR)
			self._consoleLogger.setLevel(logging.INFO)
			self._consoleLogger.setLevel(logging.DEBUG)
			
			cons = _getConsoleHandler(logging.DEBUG,self.logformat)
			cons.setFormatter(formatter)
			self._consoleLogger.addHandler(cons)
			
			# Add the log message handler to the logger
		return self._consoleLogger
	
	def _getDebugLogger(self):
		if self._dbgLogger == None and self.dbgfile:
			self._dbgLogger = logging.getLogger('BibDebugLogger')
			hdlr = RotatingFileHandler(self.dbgfile, maxBytes=self.maxBytes, backupCount=self.backupCount)
			formatter = BibLogFormatter(fmt=str(self.logformat))
			hdlr.setFormatter(formatter)
			self._dbgLogger.setLevel(logging.ERROR)
			self._dbgLogger.setLevel(logging.INFO)
			self._dbgLogger.setLevel(logging.DEBUG)
			self._dbgLogger.addHandler(hdlr) 
			
			# Add the log message handler to the logger
		return self._dbgLogger
	
	def _getInfoLogger(self):
		if self.singlefile and self.infofile:
			return self._getDebugLogger()
		if self._infoLogger == None:
			self._infoLogger = logging.getLogger('BibInfoLogger')
			hdlr = RotatingFileHandler(self.infofile, maxBytes=self.maxBytes, backupCount=self.backupCount)
			formatter = BibLogFormatter(fmt=str(self.logformat))
			hdlr.setFormatter(formatter)
			self._infoLogger.addHandler(hdlr) 
			self._infoLogger.setLevel(logging.INFO)
			# Add the log message handler to the logger
		return self._infoLogger

	def exc(self,msgId,params):
		msg = BibMessageLog(msgId,params,self.extendedformat)
		if self.level <= LEVELS["ERROR"]: 
			if self.errfile:
				self._getErrLogger().error(" Exception "+str(msg), exc_info=1)
			if self.logInConsole and not self.quiet :
				self._getConsoleLogger(self.logformat).error(" Exception "+str(msg), exc_info=1)
	
	def log(self,inMsgId,params=[]):
		'''
		display an application message with a standard formating. 
		condition :
		A message must be created with the bib web interface, 
		first check if your message does not already exists, then if not, create it and
		use the bibSyncTool to generate the python message file with global log message constants.
		:param msgId: this argument must be a valid id message
		'''
		msgId=inMsgId
		if isinstance(msgId, str):
			msgId=self.msgconf[msgId]
		msg = BibMessageLog(msgId,params,self.extendedformat)
		message=str(msg)

		if msg.type == "ERROR" :
			if self.level <= int(LEVELS["ERROR"]): 
				if self.errfile :
					self._getErrLogger().error(message)
					if self.dbgfile:
						self._getDebugLogger().error(message)
				if self.logInConsole and not self.quiet:
					self._getConsoleLogger().error(message)

		elif   msg.type == "DEBUG" :
			if self.level <= LEVELS["DEBUG"]: 
				if self.dbgfile:
					self._getDebugLogger().debug(message)
				if self.logInConsole and not self.quiet:
					self._getConsoleLogger().debug(message)

		elif   msg.type == "INFO" :
			if self.level <= LEVELS["INFO"]: 
				if self.infofile:
					self._getInfoLogger().info(message)
					if self.dbgfile:
						self._getDebugLogger().info(message)
				if self.logInConsole and not self.quiet:
					self._getConsoleLogger().info(message)
			
	def debug(self,msgStr):
		'''
		display a simple application debug message with a standard formating. 
		pre-condition :
		this function uses a predefined message id to get standard format, 
		so please use the bibSyncTool to generate the python message file 
		with log message constants.
			
		:param msgStr: the debug message string to display
		'''
		if 'BIB_DBG_DEFAULT_MESSAGE' in self.msgconf.__dict__:
			self.log(self.msgconf.BIB_DBG_DEFAULT_MESSAGE,params=[msgStr])
		else: 
			self.log(0,params=[msgStr])


######################################################################################
######################################################################################
################# THIS PART IS FOR CALLING FROM SH ###################################
######################################################################################
######################################################################################
	
from optparse import OptionParser
checkoptions=False
def startCmd(args):
	desc="""
	Ce programme python permet de logger dans un fichier une chaine formatée
	"""
	parser = OptionParser("%prog -h pour afficher l'aide",description=desc)

	parser.add_option("-s", "--singlefile", dest="singlefile",
					help="One common log file",metavar='<file>')

	parser.add_option("-e", "--errlogfile", dest="errlogfile",
					help="The log file",metavar='<file>')

	parser.add_option("-d", "--dbglogfile", dest="dbglogfile",
					help="The debug log file",metavar='<file>')

	parser.add_option("-n", "--infologfile", dest="infologfile",
					help="The info log file",metavar='<file>')

	parser.add_option("-c", "--msgcfgfile", dest="msgcfgfile",
					help="The Messages' configuration file",metavar='<file>')
	
	parser.add_option("-a", "--proginfo", dest="proginfo",
				help="List of information to substitute (PID,threadName,line,...) : 'key:value' separated by ';' example : PID:1246; cles="+str(ginfo.keys()), metavar="{list}")
	
	parser.add_option("-m", "--msgid", dest="msgid",
					help="The Message to log",metavar='<msgid>')

	parser.add_option("-p", "--msgparams", dest="msgparams",
					help="The Message parameters",metavar='<msgparams>')
	
	parser.add_option("-g", "--logInConsole", dest="logInConsole",
					help="Log in consol (defaut = 1) 0 to avoid logging on the screen",metavar='logInConsole=[0,1]')

	parser.add_option("-l", "--level", dest="level",
					help="Debug level (DEBUG,ERROR,INFO) ERROR level only log errors, DEBUG logs everything",metavar='level=[DEBUG,INFO,ERROR]')

	parser.add_option("-b", "--maxBytes", dest="maxBytes",
					help="Max size for a log file",metavar='<maxBytes>')

	parser.add_option("-u", "--backupCount", dest="backupCount",
					help="Amount of rotation file for a given log file",metavar='<backupCount>')

	(options, args) = parser.parse_args()
	CFG_LOG={}
	"""	
	"-singlefile":"log2/all-logs.log",
	"multi-infofile":"log2/msglogs.log",
	"multi-errfile":"log2/errorlogs.log",
	"-multi-dbgfile":"log2/debugLogs.log",
	"rotate-maxBytes":"5000",
	"rotate-backupCount":3,
	"logInConsole":1,
	"level":"INFO"
	"""
	if options.backupCount :
		CFG_LOG['rotate-backupCount']=options.backupCount

	if options.maxBytes :
		CFG_LOG['rotate-maxBytes']=options.maxBytes

	if options.errlogfile :
		CFG_LOG['multi-errfile']=options.errlogfile
	
	if options.dbglogfile:
		CFG_LOG['multi-dbgfile']=options.dbglogfile

	if options.logInConsole:
		CFG_LOG['logInConsole']=options.logInConsole

	if options.level:
		CFG_LOG['level']=options.level

	if options.infologfile:
		CFG_LOG['multi-infofile']=options.infologfile

	if not options.msgcfgfile:
		print ("--msgcfgfile: Please specify the Messages' configuration file")
		return
	
	if not options.proginfo:
		print ("--proginfo: Please specify the keywords list to susbstitute (PID,threadName,line,...)")
		return
	
	if not options.msgid:
		print ("--msgid: Please specify the Message id to log")
		return
	
	options.msgparams=options.msgparams.split(";")
	ginfo['funcName']="-"
	for tup in options.proginfo.split(";"):
		[k,v]= tup.split(":")
		if k in ginfo:
			if v:
				ginfo[k]=v

	msgconf = loadMsgConf(options.msgcfgfile)
	testlogger = BibLogger(CFG_LOG,msgconf)
	if options.msgid in msgconf :
		testlogger.log(msgconf[options.msgid], params=options.msgparams)
	else:
		print ("Error",options.msgid, " not found in configuration file")

def logExc():
	pass

if __name__ == "__main__":
	startCmd(sys.argv)
