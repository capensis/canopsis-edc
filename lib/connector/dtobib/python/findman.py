# -*- coding: utf-8 -*-
#Superzip.
#outil de purge generic
#permet de faire d'appliquer plusieurs filtres de recherches �volu�s dans l'arborescence s�lectionn�e

_PURGEMAN_VERSION_ = '1.0.5'

"""
import logging

import logging
import logging.handlers

logging.getLogger('AuditLogger')
logging.getLogger('StatLogger')
logging.getLogger('PrintLogger')
"""


import os,  shutil,  sys
from optparse import OptionParser
import datetime
import fnmatch
import time

if (sys.version_info[0] > 1 and sys.version_info[1] > 6) or (sys.version_info[0] >2) :
	pass
	#print("python version :"+str(sys.version_info))
else:
	print ("#### FATAL ERROR : ###\n ce programme ne fonctionne qu'à partir de la version 2.7 de python,\n version actuelle "+str(sys.version_info))
	sys.exit(-1)
sys.path.append("lib")
try:
	import bibutils
except:
	if "DTO_BIB_HOME" in os.environ:
		DTO_BIB_HOME=os.environ["DTO_BIB_HOME"]
		sys.path.append(DTO_BIB_HOME)
	else:
		print ("#### FATAL ERROR : ###\nDTO BIB n'a été trouvée ni dans le path et la var env DTO_BIB_HOME n'est pas renseignée")
		sys.exit(-1)
try:
	import bibutils
except :
		print ("#### FATAL ERROR : ###\nDTO BIB n'a été trouvée ni dans le path ni dans la var env DTO_BIB_HOME")
		exit(0)

import biblog
from biblog import loadMsgConf
from base64 import encode
#import threading
import multiprocessing
import subprocess
def print2(msg,*args):
	#print msg,args
	pass

try:
	import queue
except ImportError:
	import Queue as queue
CSVFORMAT = "$(processId);$(startDate);$(purgeId);$(hostId);$(s_extends);$(processedFid);$(basedir);$(name);$(size);$(ownername);$(groupname);$(mode);$(modifdate);$(createdate);$(accessdate);$(filetype);$(processedAction)"


class g_context(object):
	options = None
	purgelogger = None
	printLogger = None
	auditLogger = None
	statLogger = None
	auditlogformat = ""
	auditdateformat = ""
	starttime=0
	#debug_walk=False
	#debug_walk=True
	follow_link_opt = True
	nbProcessedFiles = 0
	nbProcessedDirs = 0
	globalInfo = None
	
	#idprocess;dttrt;idpurge;idpurgehost;idpurgerep;idpurgefiltre;nmrep;nmfic;nboct;nmuid;nmgid;cdmod;dtficcrea;dtficmaj
	filterGroupDebugPrint = False

def getTDateString(t):
	dt=datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
	return dt


def _getAuditLogger(context):
	auditLogger=context.auditLogger 
	options=context.options
	if not auditLogger :
		if options.matchfile: 
			auditLogger = logging.getLogger('AuditLogger')
			worker="mainProcess"
			if context.globalInfo:
				if 'currentWorker' in context.globalInfo:
					worker=context.globalInfo['currentWorker']
			if options.verbose:
				print2(worker+" take logger file :",options.matchfile)
			context.audithandler = logging.FileHandler(options.matchfile)
			#handler = logging.handlers.RotatingFileHandler(options.matchfile, maxBytes=100000, backupCount=0)
			auditLogger.addHandler(context.audithandler)
			auditLogger.setLevel(logging.DEBUG)
			context.auditLogger=auditLogger

	return auditLogger

def _getStatLogger(context):
	statLogger=context.statLogger
	options=context.options
	if not statLogger :
		if options.unmatchfile: 
			statLogger = logging.getLogger('StatLogger')
			if options.verbose:
				print2("creating logger in file :",options.unmatchfile)
			context.stathandler = logging.FileHandler(options.unmatchfile)
			#handler = logging.handlers.RotatingFileHandler(options.matchfile, maxBytes=100000, backupCount=0)
			statLogger.addHandler(context.stathandler)
			statLogger.setLevel(logging.DEBUG)
			context.statLogger=statLogger

	return statLogger

def _getPrintLogger(context):
	printLogger=context.printLogger
	options=context.options
	if not printLogger :
		printLogger = logging.getLogger('PrintLogger')
		#print "actionsfile",options.actionsfile
		if options.actionsfile: 
			hdlr = logging.FileHandler(options.actionsfile)
			formatter = logging.Formatter("", "")
			hdlr.setFormatter(formatter)
			printLogger.addHandler(hdlr)
		if not options.quiet:
			console = logging.StreamHandler()
			formatter = logging.Formatter("", "")
			console.setFormatter(formatter)
			printLogger.addHandler(console)
		printLogger.setLevel(logging.DEBUG)
	return printLogger

def printlog(context,pr):
	return 0
	print pr
	if _getPrintLogger(context):
		_getPrintLogger(context).error(pr)

def auditlog(context,csv):
	print csv
	#_getAuditLogger(context).error(csv)

def statlog(context,csv):
	return 0
	statlog=_getStatLogger(context)
	if statlog:
		statlog.error(csv)


def getPurgeLogger(context):
	if context.options.logfile :
		CFG_LOG = {
				"singlefile":context.options.logfile,
				"logInConsole":1,
				"level":"DEBUG"
		}
		#print "not yet implemented, please use var environment BIB_MSGCONF_PATH"
		purgelogger = biblog.BibLogger(confs=CFG_LOG,quiet=context.options.quiet)
		context.purgelogger=purgelogger
	else:
		if context.options.logconffile :
			#print "not yet implemented, please use var environment BIB_MSGCONF_PATH"
			_confs = loadMsgConf(context.options.logconffile)
			purgelogger = biblog.BibLogger(confs=_confs,quiet=context.options.quiet)
			context.purgelogger=purgelogger
		else:
			purgelogger = biblog.BibLogger(quiet=context.options.quiet)
			context.purgelogger=purgelogger
	return purgelogger

def purgelog(context,msg):
	return 0
	print "purgelog:",msg
	purgelogger=context.purgelogger
	#if context.options.debug_walk:		print (msg)
	if not purgelogger:
		purgelogger=getPurgeLogger(context)
		#sys.stderr.write("purgelogger must not be null")
	purgelogger.log("CPM_INFO_DELETE_FILE",msg)

def purgelogerror(context,msg,e=None):
	return 0
	print "purgelogerror:",msg
	if context:
		purgelogger=context.purgelogger
		if e:
			msg+=str(e)
		purgelogger.log("CPM_INFO_DELETE_FILE",msg)
		if context.options.verbose:
			print2("###"+msg)
	else:
		sys.stderr.write("g_purgeloggerror must not be null")
		
def getvalue(adict, attr, resp=None,values=None):
	ret=resp
	if adict:
		if attr in adict:
			ret=adict[attr]
			if values:
				if ret in values:
					ret=values[ret]
	return ret

registredActions={
				"deletefiles":{"filetype":"deletefiles"},
				"deletedirs":{"filetype":"deletedirs"}
				}
registredFilters={}
fsfilter_instance_count=0

def registerFilter(afilter):
	if afilter.id not in registredFilters:
		registredFilters[afilter.id]=afilter


def getRegistredFilter(s_filter):
	if s_filter in registredFilters:
		return registredFilters[s_filter]
	return None

def getRegistredAction(s_action):
	if s_action in registredActions:
		return s_action
	return None


def eval_exptime(time_exp,context):
	repexpr=time_exp.replace("y","*"+str(31536000))
	repexpr=repexpr.replace("m","*"+str(2592000))
	repexpr=repexpr.replace("d","*"+str(86400))
	repexpr=repexpr.replace("h","*"+str(3600))
	repexpr=repexpr.replace("min","*"+str(60))
	repexpr=repexpr.replace("sec","*"+str(1))
	try:
		result=eval(repexpr)
		return result
	except (ValueError, SyntaxError):
		#print "#ERROR cannot eval ",time_exp
		purgelogerror(context,"#ERROR cannot eval " + str(time_exp) )
	return None


class FsFilter(object):
	ACTION_TYPE={'printfiles':"FILE_ACTION",
				'deletedirs':"DIR_ACTION",
				'deletefiles':"FILE_ACTION",
				'deletedirs':"DIR_ACTION"
				}
	id = None
	rootdir = None
	folders = None
	parentfilter=None
	walked = None
	size_gt = None
	size_lt = None
	recursive = False
	exclude = None
	search_pattern = None
	parent_pattern = None
	action = None
	sortbytime = None
	sortbysize = None
	sortbyname = None
	keep_nbfiles = None
	age_gt = None
	age_gt_exp = None
	age_lt_exp=None
	age_lt = None
	date_max = None
	date_min = None
	extends = None
	has_files = None
	has_subdirs = None
	has_processedfiles = None
	has_processeddirs = None
	is_empty = None
	abstract = False
	secondpass = False
	filterchilds=None
	options=None
	SORT_TYPES={'ASC':True,'DESC':False}
	BOOLEAN_TYPE={"True":True,"False":False}
	r_alreadyProcessed="alreadyProcessed"
	r_nameNotMatched="nameNotMatched"
	r_excluded="excluded"
	r_folderNotInRange="folderContentNotInRange"
	r_sizeNotInRange="sizeNotInRange"
	r_ageNotInRange="ageNotInRange"
	r_matched="matched"
	s_extends=""
	def __init__(self, dictfilter,context):
		global fsfilter_instance_count
		fsfilter_instance_count+=1
		self.context=context
		self.options=context.options
		s_extends = getvalue(dictfilter, "extends_filter", "")
		
		if s_extends:
			extends = getRegistredFilter(s_extends)
			if extends is not None:
				#self.s_extends=self.extends.id
				for k in extends.__dict__:
					setattr(self, k, getattr(extends, k))
				self.extends=extends
		self.s_extends=s_extends
		#print ("################ self.s_extends="+self.s_extends)
		self.walked=0
		self.id = getvalue(dictfilter, 'id', 'filter'+str(fsfilter_instance_count))
		self.secondpass = getvalue(dictfilter, 'secondpass', self.secondpass)
		self.rootdir = getvalue(dictfilter, 'rootdir', self.rootdir)
		if self.rootdir:
			self.folders = self.rootdir.replace("\\","/").split("/")
		self.has_processedfiles = getvalue(dictfilter, 'has_processedfiles', self.has_processedfiles,self.BOOLEAN_TYPE)
		self.has_processeddirs = getvalue(dictfilter, 'has_processeddirs', self.has_processeddirs,self.BOOLEAN_TYPE)
		self.has_files = getvalue(dictfilter, 'has_files', self.has_files,self.BOOLEAN_TYPE)
		self.has_subdirs = getvalue(dictfilter, 'has_nodir', self.has_subdirs,self.BOOLEAN_TYPE)
		self.is_empty = getvalue(dictfilter, 'is_empty', self.is_empty,self.BOOLEAN_TYPE)
		if not self.is_empty:
			self.is_empty = False

		#print ("filtre self.is_empty"+str(self.is_empty))
		self.size_gt = getvalue(dictfilter, 'size_gt', self.size_gt)
		self.size_lt = getvalue(dictfilter, 'size_lt', self.size_lt)
		self.date_max = getvalue(dictfilter, 'date_max', self.date_max)
		self.date_min = getvalue(dictfilter, 'date_min', self.date_min)
		self.recursive = getvalue(dictfilter, 'recursive', self.recursive,self.BOOLEAN_TYPE)
		self.parent_pattern = getvalue(dictfilter, 'parent_pattern', self.parent_pattern)
		self.abstract = False  #ne doit pas etre herite
		self.abstract = getvalue(dictfilter, 'abstract', self.abstract,self.BOOLEAN_TYPE)
		self.action= getvalue(dictfilter, 'action', self.action)
		self.actiontype = "NONE"
		if self.action:
				if not self.action in self.ACTION_TYPE:
					if self.options.debug_walk: 
						print2("action type not found")
				else:
					if self.options.debug_walk:
						print2("action ok")
					self.actiontype=self.ACTION_TYPE[self.action]
						
		self.search_pattern = getvalue(dictfilter, 'search_pattern', self.search_pattern)
		self.sortbyname = getvalue(dictfilter, 'sortbyname', self.sortbyname,self.SORT_TYPES)
		#if sortbyname in self.SORT_TYPES:			self.sortbyname = sortbyname
		self.sortbysize = getvalue(dictfilter, 'sortbysize', self.sortbysize ,self.SORT_TYPES)
		self.sortbytime  = getvalue(dictfilter, 'sortbytime', self.sortbytime ,self.SORT_TYPES)
		keep_nbfiles = getvalue(dictfilter, 'keep_nbfiles', 0)
		if keep_nbfiles:
			truncsize = int(keep_nbfiles )
			if truncsize:
				self.keep_nbfiles = truncsize 
		age_lt_exp = getvalue(dictfilter, 'age_lt', "")
		if age_lt_exp:
			self.age_lt=eval_exptime(age_lt_exp,context)
			self.age_lt_exp = age_lt_exp
		age_gt_exp = getvalue(dictfilter, 'age_gt', self.age_gt)
		if age_gt_exp:
			self.age_gt=eval_exptime(age_gt_exp,context)
			self.age_gt_exp=age_gt_exp
		exclude_str = getvalue(dictfilter, 'exclude_filter', None)
		if exclude_str=='':
			self.exclude = None
		else:
			if isinstance(exclude_str, str):
				self.exclude  = getRegistredFilter(exclude_str)
			elif isinstance(exclude_str, dict):
				self.exclude = FsFilter(exclude_str,self.context)
		
		registerFilter(self)
	
	def __repr__(self):
		kind=""
		if self.search_pattern:
			kind+="'"+self.search_pattern+"'"
		if self.age_gt_exp:
			kind+=", +"+str(self.age_gt_exp)
		if self.age_lt_exp:
			kind+=" -"+str(self.age_lt_exp)
		return "f."+self.id+"("+kind+")" 
	
	def sort_by_name(self,infolist,sorttype):
		infolist.sort(key=lambda x: x.name,reverse=self.SORT_TYPES[sorttype])
	
	def sort_by_time(self,infolist,sorttype):
		infolist.sort(key=lambda x: x.mtime,reverse=self.SORT_TYPES[sorttype])
	
	def sort_by_size(self,infolist,sorttype):
		infolist.sort(key=lambda x: x.size,reverse=self.SORT_TYPES[sorttype])

	def checkGreaterOrNull(self,b_cond,value,bmatch):
		match = bmatch
		if match:
			if b_cond is not None:
				if b_cond == True:
					match=value>0
				else:
					match=value==0
		return match
	
	def checkFolderNbContent(self,infofile):
		#nbFiles	nbDirs	nbProcessedFiles	nbProcessedDirs
		#has_files 	has_subdirs 	has_processedfiles 	has_processeddirs	is_empty
		match=True
		#infofile.reason="has%dFiles"% infofile.nbFiles
		if infofile.nbFiles >= 0 and self.has_files:
			infofile.reason="has%dFiles"% (infofile.nbFiles)
			match=self.checkGreaterOrNull(self.has_files,infofile.nbFiles,True)
		if infofile.nbDirs >= 0 and self.has_subdirs:
			infofile.reason="has%dSubDirs"%(infofile.nbDirs)
			match=self.checkGreaterOrNull(self.has_subdirs,infofile.nbDirs,match)
		if infofile.nbFiles >= 0 and self.is_empty and match:
			nbfiles=infofile.nbFiles 
			if infofile.nbDirs >= 0:
				nbfiles=infofile.nbFiles + infofile.nbDirs
			infofile.reason="has%dfiles_MustBeEmpty"%(nbfiles)
			match=nbfiles==0
		if infofile.nbProcessedFiles>=0 and self.has_processedfiles:
			infofile.reason="has%dProcessedFiles"%(infofile.nbProcessedFiles)
			match=self.checkGreaterOrNull(self.has_processedfiles,infofile.nbProcessedFiles,match)
		if infofile.nbProcessedDirs >= 0 and self.has_processeddirs:
			infofile.reason="has%dProcessedDirs"%(infofile.nbProcessedDirs)
			match=self.checkGreaterOrNull(self.has_processeddirs,infofile.nbProcessedDirs,match)
		return match
			
	def addChild(self,achild):
		if self.parentfilter!=achild:
				if self.filterchilds is None:
					self.filterchilds=[]
				self.filterchilds.append(achild)
				achild.parentfilter = self
				if self.context.options.debug_walk:
					#PHIL print "		",self.id,".childs=",self.filterchilds
					if self.options.verbose:
						print2("		"+self.id+".childs="+unicode(self.filterchilds))
					purgelog(self.context,"		"+self.id+".childs="+unicode(self.filterchilds))
				if achild.filterchilds:
					for ch in achild.filterchilds:
						self.addChild(ch)
					achild.filterchilds=None
						
		else:
			if self.context.options.debug_walk:print2("cannot add self as child")
			
		
	def checksize(self,infofile):
		match=True
		greaterthan=None
		if self.size_gt:
			match=False
			greaterthan=self.size_gt
			if infofile.size> greaterthan:
				match=True
		if self.size_lt:
			if greaterthan==None or greaterthan!=None and match:
				lessthan=self.size_lt
				match=False
				if infofile.size < lessthan:
					match=True
		return match

	def checkage(self,infofile):
		match=True
		infofile.agematch=""
		greaterthan=None
		if self.age_gt:
			match=False
			greaterthan=self.age_gt
			if infofile.age > greaterthan:
				match=True
				infofile.agematch=str(infofile.age)+" >gt " + str(greaterthan)
		if self.age_lt:
			if greaterthan==None or greaterthan!=None and match:
				lessthan=self.age_lt
				match=False
				if infofile.age < lessthan:
					match=True
					infofile.agematch=str(infofile.age)+" < " + str(greaterthan)
		return match
	
	def checkname(self,infofile,pattern):
		match=False
		if pattern:
			if pattern!="":
				if fnmatch.fnmatch(infofile.name, pattern):
					match=True
		return match
	
	def checkdirname(self,fstree):
		match=True
		root=""
		if 'path' in fstree:
			root=fstree["path"]
		if 'name' in fstree:
			if self.parent_pattern:
				match=False
				parent_pattern=self.parent_pattern
				filter_root=root.replace(self.rootdir,"")
				for dirname in filter_root.split(os.path.sep):
					if fnmatch.fnmatch(dirname, parent_pattern):
						match=True
						break;
		return match
	def applyfilter(self,fstree):
		matchedfiles=[]
		subdirmatches=[]
		matcheddirs=[]
		excludedfs=None
		if self.exclude:
			excludedfs=self.exclude.applyfilter(fstree)
		parentdirmatch=self.checkdirname(fstree)
		reason="outOfFilter"
		if parentdirmatch :
			if 'files' in fstree and self.actiontype == "FILE_ACTION":
				excludedfiles=getvalue(excludedfs,'files',[])
				matched=False
				for infofile in fstree['files']:
					infofile.reason=self.r_alreadyProcessed
					if self.options.debug_walk:
						print2("check proc filename "+infofile.name)
					if not infofile.processedFid:
						infofile.checkedFid=self.id
						reason=self.r_nameNotMatched
						if self.checkname(infofile, self.search_pattern):
							infofile.reason=self.r_excluded
							if not infofile in excludedfiles:
								infofile.reason=self.r_folderNotInRange
								if self.checkFolderNbContent(infofile):
									infofile.reason=self.r_sizeNotInRange
									if self.checksize(infofile):
										infofile.reason="age%sNotInRange"%"("+"%3.1f"%(infofile.age/86400)+"d)"
										if self.checkage(infofile):
											matchedfiles.append(infofile)
											if self.options.debug_walk:
												print2("found filename "+infofile.name)
											infofile.reason=self.r_matched
											matched=True
											#infofile.processedFid = self.id
						"""					
						if infofile.reason=self.r_matched:
							auditlog(self.context,infofile.csv(currentFilter=self))
						else:"""
						if infofile.reason!=self.r_matched and infofile.reason!=self.r_alreadyProcessed and infofile.reason!=self.r_nameNotMatched:
							statlog(self.context,infofile.csv(currentFilter=self))
						
			
			dirs=getvalue(fstree,'dirs',None)
			if dirs and self.actiontype == "DIR_ACTION":
				excludeddirs=getvalue(excludedfs,'dirs',[])
				for infofile in dirs:
					infofile.reason=self.r_alreadyProcessed
					if not infofile.processedFid:
						infofile.checkedFid=self.id
						reason=self.r_nameNotMatched
						if self.checkname(infofile, self.search_pattern):
							infofile.reason=self.r_excluded
							if not infofile in excludeddirs:
								infofile.reason=self.r_folderNotInRange
								if self.checkFolderNbContent(infofile):
									infofile.reason=self.r_sizeNotInRange
									if self.checksize(infofile):
										infofile.reason="age%sNotInRange"%"("+"%3.1f"%(infofile.age/86400)+"d)"
										if self.checkage(infofile):
											if self.options.debug_walk:
												print2("found dirname "+infofile.name)
											matcheddirs.append(infofile)
											infofile.reason=self.r_matched
											matched=True
											#infofile.processedFid = self.id
						"""if infofile.reason==self.r_matched:
							matcheddirs.append(infofile)
						else:"""
						if infofile.reason!=self.r_matched and infofile.reason!=self.r_alreadyProcessed and infofile.reason!=self.r_nameNotMatched:
							statlog(self.context,infofile.csv(currentFilter=self))
								
			
			if 0 and self.recursive:
				subdirs=getvalue(fstree,'subdirs',None)
				if subdirs:
					for subtree in subdirs:
						infofile=dirs[subtree['name']]
						matched=False
						if not infofile.processedFid:
							subdirmatch=self.applyfilter(subtree)
							if subdirmatch :
								subdirmatches.append(subdirmatch)
							
							if not matched:
								infofile.reason=reason
								statlog(self.context,infofile.csv(currentFilter=self))
							#else:								auditlog(self.context,infofile.csv(currentFilter=self))
								
		ret=None
		if parentdirmatch:
			if len(matchedfiles)>0:
				if self.sortbyname:
					self.sort_by_name(matchedfiles,self.sortbyname)
				if self.sortbysize:
					self.sort_by_size(matchedfiles,self.sortbysize)
				if self.sortbytime:
					self.sort_by_time(matchedfiles,self.sortbytime)
				if self.keep_nbfiles is not None:
					if self.keep_nbfiles > 0:
						if len(matchedfiles)>self.keep_nbfiles:
							matchedfiles = matchedfiles[0:self.keep_nbfiles]
				if len(matchedfiles)>0:
					ret={}
					ret['files']=matchedfiles
		if len(subdirmatches)>0:
			if not ret:
				ret={}
			ret['subdirs']=subdirmatches
		if matcheddirs:
			if not ret:
				ret={}
			ret['dirs']=matcheddirs
		if ret:
			ret['path']=fstree["path"]

		return ret
	
	
	def printfilesFunc(self,action,afilteredtree):
		if not afilteredtree:
			return
		if "files" in afilteredtree:
			for infofile in afilteredtree["files"]:
				printlog(self.context,"print rm "+infofile.basedir+'/'+infofile.name)
				infofile.processedAction="printfile"
				print2("print rm "+infofile.basedir+'/'+infofile.name)
				infofile.processedFid=self.id
				
		if "oldsubdirs" in afilteredtree: 
			if self.options.recursive:
				for subtreedir in afilteredtree["subdirs"]:
					self.printFunc(action,subtreedir)
				
	def printdirsFunc(self,action,afilteredtree):
		#baseStruct=getBaseFSDirStruct(afilteredtree['path'])
		#if baseStruct == None:		print "FATAL ERROR corrupted base tree"		exit(0)
		if not afilteredtree:
			return
		if "dirs" in afilteredtree:
			for infofile in afilteredtree["dirs"]:
				if 'path' in afilteredtree:
					printlog(self.context,"print rmdir "+infofile.basedir+'/'+infofile.name)
					infofile.processedAction="printdir"
					#print2("print rmdir "+infofile.basedir+'/'+infofile.name)
				infofile.processedFid=self.id
	
	
	def deletefilesFunc(self,action,afilteredtree):
		#baseStruct=getBaseFSDirStruct(afilteredtree['path'])
		#if baseStruct == None:		print "FATAL ERROR corrupted base tree"		exit(0)
		if not afilteredtree:
			return
		if "files" in afilteredtree:
			for infofile in afilteredtree["files"]:
				#print "rm",afilteredtree['path']+'/'+infofile.name,self.id
				if self.options.printactions:
					printlog(self.context,"rm1 "+infofile.basedir+'/'+infofile.name)
					infofile.processedAction="print"
					print2("rm2 "+infofile.basedir+'/'+infofile.name)
				"""
				if self.options.execaction:
					os.remove(infofile.basedir+'/'+infofile.name)
					infofile.processedAction="deletefile"
				"""	
				auditlog(self.context,infofile.csv(currentFilter=self))
				infofile.processedFid=self.id
		if "oldsubdirs" in afilteredtree:
			if self.options.recursive: 
				for subtreedir in afilteredtree["subdirs"]:
					self.deletefilesFunc(action,subtreedir)
	

	def deletedirsFunc(self,action,afilteredtree):
		if self.options.debug_walk:
			print2("enter deletedirsFunc for "+str(afilteredtree))
		#baseStruct=getBaseFSDirStruct(afilteredtree['path'])
		#if baseStruct == None:		print "FATAL ERROR corrupted base tree"		exit(0)
		if not afilteredtree:
			return
		#if self.options.printactions:self.printdirsFunc(action,afilteredtree)
		if "dirs" in afilteredtree:
			if self.options.debug_walk:
				print2("delete dir on "+str(afilteredtree["dirs"]))
			for infofile in afilteredtree["dirs"]:
				infofile.processedFid=self.id
				if self.is_empty:
					printlog(self.context,"rmdir "+infofile.basedir+'/'+infofile.name)
					infofile.processedAction="printdeldirs"
					if self.options.printactions:
						print2("rmdir2 "+infofile.basedir+'/'+infofile.name)
				else:
					infofile.processedAction="printdeltree"
					if self.options.printactions:
						print2("rmtree2 "+infofile.basedir+'/'+infofile.name)
				"""	
				if self.options.execaction:
					####phil 
					if self.is_empty:
						try:
							os.rmdir(infofile.basedir+'/'+infofile.name)
							infofile.processedAction="deletedirs"
							auditlog(self.context,infofile.csv(currentFilter=self))
						except:
							print2("match is_empty dir " + infofile.basedir+'/'+infofile.name + " RMDIR EXC NOT DELETED")
							infofile.reason="Exception"
							statlog(self.context,infofile.csv(currentFilter=self))
							pass
					else:
						try:
							shutil.rmtree(infofile.basedir+'/'+infofile.name)
							infofile.processedAction="deletedirs"
							auditlog(self.context,infofile.csv(currentFilter=self))
						except:
							print2("match dir " + infofile.basedir+'/'+infofile.name + " RMTREE EXC NOT DELETED")
							infofile.reason="Exception"
							statlog(self.context,infofile.csv(currentFilter=self))
							pass
				else:
				"""
				auditlog(self.context,infofile.csv(currentFilter=self))
				
	ACTION_FUNC={'printfiles':printfilesFunc,
			'deletedirs':printdirsFunc,
			'deletefiles':deletefilesFunc,
			'deletedirs':deletedirsFunc
			}

	def dojob(self,jobfs):
		ret=False
		stree = self.applyfilter(jobfs)
		if stree:
			if self.options.debug_walk:
				print2("action on stree  action:"+str(self.action))
			if self.action:
				if not self.action in self.ACTION_FUNC:
					if self.options.debug_walk: 
						print2("action not found")
				else:
					if self.options.debug_walk:
						print2("action ok")
					self.ACTION_FUNC[self.action](self,self.action,stree)
				ret=True
		else:
			if self.options.debug_walk:
				print2("job found no file")
		return ret

#baseFSTree=Walk("c:/program files")
#'mtime': datetime.date(1998, 12, 9),

"""
def getBaseFSDirStruct(apath):
	thestruct=baseFSTree
	rpath = apath.replace(thestruct['path'],'')
	for dirname in rpath.split(os.path.sep):
		if len(dirname)>0:
			for subsdir in thestruct['subdirs']:
				if 'name' in subsdir:
					if subsdir['name']==dirname:
						thestruct=subsdir
						break
				else:
					print "error"
	if thestruct['path']==apath:
		return thestruct
	else:
		return None

"""

class InfoFile(object):
	name=None
	basedir=""
	atime=None
	mtime=None
	ctime=None
	modifdate=None
	createdate=None
	accessdate = None
	uid=None
	ownername=None
	gid=None
	groupname=None
	islink=False
	mode=None
	processedFid=""
	checkedFid=""
	printaudit=None
	filetype=None
	size=None
	age=None
	nbFiles=-1
	nbDirs=-1
	nbProcessedFiles=-1
	nbProcessedDirs=-1
	processedAction=None
	globalInfo=None
	reason=None
	agematch=None
	def __init__(self, name,isfile,context):
		self.name = name
		self.printaudit = False
		if isfile :self.filetype='F' 
		else: self.filetype='D'
		self.globalInfo=context.globalInfo
		self.context=context
	def csv(self,csvformat=CSVFORMAT,currentFilter=None):
		self.modifdate=datetime.datetime.fromtimestamp(self.mtime)
		self.createdate=datetime.datetime.fromtimestamp(self.ctime)
		self.accessdate=datetime.datetime.fromtimestamp(self.atime)
		endtime=time.time()
		difftime = endtime - self.mtime
		#print "temps écoulé :",time.asctime( time.gmtime(difftime) ),"secondes" 
		difftuple = time.gmtime(difftime)
		self.agestr=str(difftuple)
		self.agestr= "%imois%ijours%ih%imin%isec" % ( difftuple.tm_mon -1 ,difftuple.tm_mday -1 ,difftuple.tm_hour - 1, difftuple.tm_min - 1 , difftuple.tm_sec - 1)
		msgstr= csvformat
		lastKey=""
		try:
			
			if currentFilter is not None:
				msgstr=msgstr.replace("$(s_extends)",str(currentFilter.s_extends))
				#print2("################# currentFilter s_extends"+currentFilter.s_extends)
				for k in currentFilter.__dict__:
					lastKey=k
					msgstr=msgstr.replace("$("+k+")",str(currentFilter.__dict__[k]))
			else:
				print2("################# currentFilter is None")
			for k in self.globalInfo:
				lastKey=k
				msgstr=msgstr.replace("$("+k+")",str(self.globalInfo[k]))
			for k in self.__dict__:
				lastKey=k
				msgstr=msgstr.replace("$("+k+")",str(self.__dict__[k]))
			processedAction = getattr(self, "processedAction","")
			if processedAction == "":
				if 'filetype' in currentFilter.action:
					processedAction = currentFilter.action['filetype']
				
			defaultValues={"rootdir":"","processedFid":str(currentFilter.id),"processedAction":processedAction}
			for k in defaultValues:
				lastKey=k
				msgstr=msgstr.replace("$("+k+")",str(defaultValues[k]))

		except Exception :
			err = str(sys.exc_info()[1])
			if self.context.options.verbose:
				print2("csvformat key '",lastKey,"' error ",err)
			#purgelogerror(self.context,"#### KeyError for "+msgstr+" exception:"+err)
			#purgelogerror(self.context,"##raised except in Infofile.csv "+str(msgstr)+" Exception :"+err)
			pass
		
		if self.globalInfo:
			if 'currentWorker' in self.globalInfo:
				worker=self.globalInfo['currentWorker']
		msgstr+=";"+str(self.reason)
		if 0:
			msgstr+=";"+str(self.checkedFid)+";"+str(self.agestr)+";"+worker+";"+str(self.agematch)
			if currentFilter:
				msgstr+=";"+str(currentFilter.search_pattern)
		return msgstr
	def __repr__(self):
		return self.name+"("+"%3.1f"%(self.age/86400)+"d)"
	
	
class Node(object):
	dirs=None
	files=None
	path=None

best_encoding='utf-8'
import locale
loc = locale.getdefaultlocale()
if loc[1]:
	best_encoding = loc[1]
locale_encoding=best_encoding

#voir sys.stdin.encoding
#x = raw_input("=>").decode(sys.stdin.encoding)
#os.startfile(x)
def guessEncodingAndDecode( data):
	global best_encoding
	guess_list=['utf-8','cp1252','iso8859-1']# add more if u want encoding = ‘iso8859-1′
	content = data
	try:
		content = data.decode(best_encoding)
	except:
		for best_enc in guess_list:
			try:
				best_encoding = best_enc
				content = data.decode(best_encoding)
				#print "#### decoded with ",best_encoding
				break
			except:
				pass
	import re
	if sys.version_info.major < 3:
		return re.sub(r"[^ -z_0-9,;-]","?",content)
	return content

def suppExtraChars(content):
	import re
	ret=guessEncodingAndDecode( content)
	ret=re.sub(r"[^ -z_0-9,;-]","?",ret)
	return ret


def WalkFiltering( root, recurse=1, pattern='*.*', return_folders=1 ,filters=None,context=None):
	# initialize
	options=context.options
	if context.options is None:
			print2("bad context options ########################")
	use_time = True
	use_size = True
	use_mode = True
	use_user = True
	global locale_encoding,g_follow_link_opt
	result = []
	# must have at least root folder
	try:
		names = os.listdir(root)
	except Exception :
		#print "###493 cannot listdir ",root," exception:",e
		err = str(sys.exc_info()[1])
		purgelogerror(context,"### cannot list "+root+" exception:"+suppExtraChars(err))
		return result
	# check each file
	files=[]
	dirs=[]
	subdirs=[]
	basename = os.path.basename(root)
	if options.debug_walk:
		print2("walking in "+root)
	for name in names:
		uname = guessEncodingAndDecode(name)
		try:
			if sys.version_info.major < 3:
				basedir=root.encode('utf-8')
			else:
				#basedir=str(root,'utf-8')
				basedir=root
			fullname = os.path.join(basedir, name)
			#print "browse ",fullname
			#sys.getdefaultencoding()
			#fullname = unicodedata.normalize('NFC',fullname )
			#fullname=unicode(fullname)
			# grab if it matches our pattern and entry filetype
			#for pat in pat_list:if fnmatch.fnmatch(name, pat):
			isfile=os.path.isfile(fullname)
			isdir= os.path.isdir(fullname)
			islink= os.path.islink(fullname)
			info=InfoFile(name,isfile,context)
			info.basedir=basedir
			if isdir :
				try:
					info.nbFiles = len(os.listdir(fullname))
				except:
					info.nbFiles = 0

			statinfo = None
			if not islink:
				if not os.path.exists(fullname):
					print2("error ",fullname," does not exists")
					purgelogerror(context," file  "+str(fullname)+" does not exists")
				else:
					if use_time or use_size or use_mode or use_user:
						try: 
							statinfo = os.stat(fullname)
						except Exception :
							#print "### cannot stat file ",fullname," Exception is :",e.args
							try:
								err = str(sys.exc_info()[1])
								purgelogerror(context,"### cannot stat file  "+str(fullname)+" exception:"+err)
							except :
								err = str(sys.exc_info()[1])
								print2("########### ERROR writing in log:",err)
					
			if statinfo:
				if use_time:
					ctime = statinfo.st_ctime
					info.ctime=ctime
					atime = statinfo.st_atime
					info.atime=atime
					mtime = statinfo.st_mtime
					info.mtime=mtime
					now = time.time()
					info.age=now-info.mtime
					
				if use_size :
					info.size=statinfo.st_size
				if use_mode :
					info.mode=statinfo.st_mode
				if use_user :
					info.uid=statinfo.st_uid
					info.gid=statinfo.st_gid
				
				try:
					import pwd # not available on all platforms
					import grp
					info.ownername=pwd.getpwuid(info.uid)[0]
					info.groupname = grp.getgrgid(info.gid)[0]
					# pwd.struct_passwd(pw_name='root', pw_passwd='x', pw_uid=0, pw_gid=0, pw_gecos='root', pw_dir='/root', pw_shell='/bin/bash')
				except (ImportError, KeyError):
					#print2("failed to get the owner name for", file)
					info.ownername="user("+str(info.uid)+")"
					info.groupname = "group("+str(info.gid)+")"
				
				if isfile and not islink:
					files.append(info) 
				elif (return_folders and isdir and not islink):
						info.islink=False
						dirs.append(info)
		except ValueError :
			#print "error in ",root,"exception",e
			#print "### cannot create infofile ", uname
			err = str(sys.exc_info()[1])
			purgelogerror(context,"### cannot create infofile, error in "+root+"/"+uname+" "+err)
			
			

		# recursively scan other folders, appending results
	fswalk={'dirs':dirs,'files':files,'path':root,'name':basename}
	#print "      parcours de ",root
	selected_filters=[]
	nbFilters=0
	for flt in filters:
		docalljob=False
		if not flt.abstract:
			nbFilters+=1
			if flt.rootdir:
				if not flt.recursive:
					if root==flt.rootdir:
						docalljob=True
				else:
					if root.find(flt.rootdir)==0:
						docalljob=True
			
			if docalljob and flt.parent_pattern is not None and flt.recursive:
				filter_root=root.replace(flt.rootdir,"")
				if len(filter_root)>0:
					for dirname in filter_root.split(os.path.sep):
						docalljob=False
						#matched = any(fnmatch(filename, p) for p in patterns)
						if fnmatch.fnmatch(dirname, flt.parent_pattern):
							docalljob=True
							break
				if flt.id=='filter1' and not docalljob:
					#print "filter & skip dir ",root
					pass
				else:
					pass
			if docalljob:
				selected_filters.append(flt)
				#sys.stderr.write(  "#### dojob on "+root+" with "+str(flt)+"\n");
	# return struct
	hasSecondPass = False
	nbProcessedFiles = 0
	nbProcessedDirs = 0
	nbFiles = 0
	nbDirs = 0
	#if len(selected_filters)>0:		print selected_filters," match ",root,"on",nbFilters," filters"
	#sys.stderr.write("\r                                                                                                       \r")
	for flt in selected_filters:
		if flt.secondpass:
			hasSecondPass = True
		if options.debug_walk:
			purgelog(context, "calling filter "+flt.id+" on "+root)
		flt.dojob(fswalk)
		#sys.stderr.write(".")
		#ceci va permettre au filtres une seule passe de supprimer les contenus vide
	for inf in fswalk['files']:
		if inf.processedFid:
			#mycsvformat = "%(processedFid)s  %(basedir)s/%(name)s action=%(processedAction)s:size=%(size)s:mdate=%(modifdate)s"
			#purgelog(inf.csv(csvformat=mycsvformat))
			nbProcessedFiles=+1
			if not inf.printaudit:
				inf.printaudit=True
				context.nbProcessedFiles +=1
		else:
			nbFiles=+1
			
	#met a jour le comptage des repertoires pour les filtres secondpass 
	for dr in fswalk['dirs']:
		if dr.processedFid:
			nbProcessedDirs+=1
			
			#purgelog(dr.csv(root," : "))
			#mycsvformat = "%(processedFid)s  %(basedir)s/%(name)s action=%(processedAction)s:size=%(size)s:mdate=%(modifdate)s"
			#purgelog(dr.csv(csvformat=mycsvformat))
			if not dr.printaudit:
				dr.printaudit=True
				context.nbProcessedDirs +=1
		else:
			nbDirs=+1


	fswalk['nbFiles']=nbFiles
	fswalk['nbProcessedFiles']=nbProcessedFiles
	fswalk['nbProcessedDirs']=nbProcessedDirs
	fswalk['nbDirs']=nbDirs
	if recurse:
		for info in dirs:
			if not info.processedFid:
				fullname = os.path.normpath(os.path.join(root, info.name))
				doWalkInside=False
				if options.debug_walk:
					purgelog(context,"checking filters for root "+fullname)
				for flt in filters:
					if flt.abstract:
						#print "skip abstract flt",flt.id
						pass
					else:
						if flt.rootdir:
								if fullname.find(flt.rootdir)==0:
									doWalkInside=True
									if options.debug_walk:
										purgelog(context,"detect flt.id="+flt.id+"("+flt.rootdir+") path is eligible")
									break;
								elif flt.rootdir.find(fullname)==0:
									doWalkInside=True
									if options.debug_walk:
										purgelog(context,"flt.id="+flt.id+"("+flt.rootdir+") path is eligible")
									break;
								else:
									#print "skip flt",flt.id,flt.rootdir
									pass
						else:
							purgelogerror(context,"ERROR : "+flt.id+" has no rootdir")
				if doWalkInside:
					if info.islink:
						purgelog(context,"Walking in symblic link "+fullname)
					res=WalkFiltering( fullname, recurse, pattern, return_folders ,filters=filters,context=context)
					if 'nbFiles' in res:
						info.nbFiles+=res['nbFiles']
						info.nbDirs+=res['nbDirs']
						info.nbProcessedFiles+=res['nbProcessedFiles']
						info.nbProcessedDirs+=res['nbProcessedDirs']
					if hasSecondPass:
						subdirs.append(res)
					else:
						res=None
				else:
					#print "      skip dir",fullname
					pass
		if len(subdirs)>0:
			fswalk['subdirs']=subdirs

	if hasSecondPass:
		for flt in selected_filters:
			if flt.secondpass:
				flt.dojob(fswalk)

	if not 'nbFiles' in fswalk:
		fswalk['nbFiles']=0
	return fswalk

g_thread_names=[]
MULTIPROCESS=multiprocessing.Process

class filterWorker(MULTIPROCESS):
	filter_queue = None
	globalInfo=None
	options=None
	options=None
	def __init__(self,procID, name, counter,queue,options,globalInfo):
		# base class initialization
		MULTIPROCESS.__init__(self)
		self.filter_queue=queue
		self.ProcID = procID
		self.name = name
		self.kill_received = False
		self.options=options
		self.globalInfo=globalInfo
	def run(self):
		global g_context
		"""		
		logging.getLogger('AuditLogger')
		logging.getLogger('StatLogger')
		logging.getLogger('PrintLogger')
		"""
		g_context.options=self.options
		self.globalInfo["currentWorker"]=self.name
		g_context.globalInfo=self.globalInfo
		

		#g_context.debug_walk=self.globalInfo['debug_walk']
		print2("_______________start "+self.name+": filter_queue size "+str(self.filter_queue.qsize())+" ____________________")

		while not self.kill_received:
		# get a task 
			flt=None
			try:
				flt = self.filter_queue.get_nowait()
				if self.options.debug_walk:
					print2("found a filter "+str(flt))
			except queue.Empty:
				if self.options.debug_walk:
					print2("Queue empty ")
				break
			
			if flt is not None:
				if flt.filterchilds is not None:
					if self.options.verbose:
						print2("WalkFiltering '"+flt.rootdir+"' witdh filters"+str([flt]+flt.filterchilds))
					purgelog(g_context,"WalkFiltering '"+flt.rootdir+"' witdh filters"+str([flt]+flt.filterchilds))

					WalkFiltering(flt.rootdir,filters=[flt]+flt.filterchilds,context=g_context)
					for f in flt.filterchilds:
						f.walked=1;
				else:
					if self.options.verbose:
						print2("WalkFiltering '"+flt.rootdir+"' witdh filters"+str([flt]))
					purgelog (g_context,"WalkFiltering '"+flt.rootdir+"' witdh filters"+str([flt]))
					WalkFiltering(flt.rootdir,filters=[flt],context=g_context)
				flt.walked=1
		if self.options.verbose:
			print2(" <- "+ self.name+"finished")
			print2("_______________end "+self.name+": filter_queue size "+str(self.filter_queue.qsize())+" ____________________")
"""
		_getAuditLogger(g_context)
		g_context.audithandler.flush()
		g_context.audithandler.close()

		_getStatLogger(g_context)
		g_context.stathandler.flush()
		g_context.stathandler.close()
		purgelog (g_context," <- "+ self.name+"finished")
"""

def startPurge(jsonfilters,context):
	global MULTIPROCESS
	options=context.options
	g_starttime=time.time()
	globalInfo={}
	globalInfo["processId"]=os.getpid()
	globalInfo["purgeId"]=jsonfilters["purgeId"]
	globalInfo["hostId"]=jsonfilters["hostId"]
	startdate=getTDateString(g_starttime)
	globalInfo["startDate"]=str(startdate)
	filters=[]
	rootdirs=[]
	groups=[]
	maxfoldlen = 0
	for jsfilter in jsonfilters['filters']:
		flt=FsFilter(jsfilter,context)
		filters.append(flt)
		if len(flt.folders)>maxfoldlen:
			maxfoldlen = len(flt.folders)
		if not flt.abstract:
			if flt.rootdir is not None:
				rootdirs.append(flt.rootdir)
			else:
				if context.options.verbose:
					print2("#ERROR ROOTDIR not defined in filter")
				purgelogerror(context,"#ERROR ROOTDIR not defined in filter")
				exit(0)
	for newparentflt in filters:
		newparentdir = newparentflt.rootdir
		if options.debug_walk:
			print2("check parent",newparentflt,newparentflt.rootdir)
		if not newparentflt.abstract: 	
			for flt in filters:
				if not flt.abstract and not flt==newparentflt:
					if options.debug_walk:
						print2("	check",flt,flt.rootdir)
					if newparentflt.recursive:
						match=flt.rootdir.find(newparentdir)==0
					else:
						match=flt.rootdir==newparentdir
					if match:
						oldparentflt = flt.parentfilter
						#le nouveau parent contient ce filtre
						if flt.parentfilter is None:
							#il n'a pas de parent, on lui en donne un
								if options.debug_walk:
									print2("	--> ",newparentflt,"addChild ",flt)
								newparentflt.addChild(flt)
						else:
							if options.debug_walk:
								print2("	==> ",flt,"has a parent rootdir: ",flt.parentfilter.rootdir)
							#il a deja un parent et la on a 2 cas
							if oldparentflt.rootdir.find(newparentdir)==0:
								#l'ancien parent contient le nouveau
								if options.debug_walk:
									print2("	==> ",flt," a un parent ",oldparentflt)
									print2("	==> ",newparentflt,"addChild ",oldparentflt," devrait aussi ajouter ",flt)
								newparentflt.addChild(oldparentflt)
								if options.debug_walk:
									print2("les childs du nouveau parents sont ",newparentflt.filterchilds)
							else:
								if newparentdir.find(oldparentflt.rootdir)==0:
									newparentflt.addChild(oldparentflt)
								pass
								"""if newparentdir.find(oldparentflt.rootdir)==0:
									#l'ancien parent est inclu dans le nouveau parent
									#on rectifie le tir, 
									oldparentflt.parentfilter = newparentflt
									flt.parentfilter = newparentflt
									#et on met a jour pour les 2 filtres
									oldparentflt.filterchilds.remove(flt)
									newparentflt.filterchilds.append(oldparentflt)
									newparentflt.filterchilds.append(flt)"""
						break;
	if options.debug_walk:print2("\n\n")
	# load up work queue
	filter_queue = multiprocessing.Queue()
	print2("_______________first filter_queue size "+str(filter_queue.qsize())+" ____________________")
	for flt in filters:
		if not flt.abstract:
			if flt.filterchilds:
				#ROOTPATH = os.path.commonprefix(rootdirs)
				#purgelog("start purge from ROOTPATH="+ROOTPATH)
				purgelog(context,"queue '"+flt.rootdir+"' witdh filters"+str([flt]+flt.filterchilds))
				if options.debug_walk:
					print2("queue '"+flt.rootdir+"' witdh filters"+str([flt]+flt.filterchilds))
				filter_queue.put(flt)
				
			else:
				if flt.parentfilter is None:
					purgelog(context,"queue mono filter'"+flt.rootdir+"' witdh filters"+str([flt]))
					if options.debug_walk:
						print2("queue mono filter '"+flt.rootdir+"' witdh filters"+str([flt]))
					filter_queue.put(flt)
	#nbthreads=1
	if context.options.nbtreads is not None:
		nbthreads=int(context.options.nbtreads)
	if nbthreads==1:
		MULTIPROCESS=object
	
	print2("_______________before run filter_queue size "+str(filter_queue.qsize())+" ____________________")
	time.sleep(1)

	if nbthreads>1:
		nb=nbFlt=filter_queue.qsize()
		if nbFlt<nbthreads:
			nb=nbFlt
		for indx in range(nb):
			if context.options.verbose:
				print2("create process walkthread_"+str(indx))
			purgelog(context,"create process walkthread_"+str(indx))
			worker = filterWorker("WkProcess"+str(indx), "PurgeWorker"+str(indx), indx,filter_queue,context.options,globalInfo)
			worker.start()
			time.sleep(1)
	else:
			if context.options.verbose:
				print2("nbthreads=1 use current process for worker!")
			purgelog(context,"nbthreads=1 use current process for worker!")
			worker = filterWorker("WkProcess"+str(0), "PurgeMainWorker", 0,filter_queue,context.options,globalInfo)
			worker.run()

	if nbthreads>0:
		if context.options.verbose:
			print2("waiting ",nbthreads,"threads to start")
		purgelog(context,"waiting "+str(nbthreads)+"threads to start")
		time.sleep(2)
	time_count=0
	if nbthreads>0:
		nbChilds=100
		while nbChilds>0:
			childs=multiprocessing.active_children()
			nbChilds=len(childs)
			if nbChilds > 0:
				if context.options.verbose:
					print2("waiting ",nbChilds,"process to terminate ",childs)
				time.sleep(2)
				time_count+=1
	if context.options.verbose:
		print2("main func terminated")
		print2("_______________after main filter_queue size "+str(filter_queue.qsize())+" ____________________")

	"""
	_getAuditLogger(context)
	context.audithandler.flush()
	context.audithandler.close()

	_getStatLogger(context)
	context.stathandler.flush()
	context.stathandler.close()
	"""
	
	endtime=time.time()
	difftime = endtime - g_starttime 
	#print "temps écoulé :",time.asctime( time.gmtime(difftime) ),"secondes" 
	difftuple = time.gmtime(difftime)
	if context.nbProcessedFiles>0:
		purgelog(context,str(context.nbProcessedFiles)+" files processed")
	if context.nbProcessedDirs>0:
		purgelog(context,str(context.nbProcessedDirs)+" dirs processed")
	
	strp= "temps ecoule est de %i heures %i minutes %i secondes" % ( difftuple.tm_hour, difftuple.tm_min, difftuple.tm_sec)
	#sys.stderr.write(strp+ '\n')
	if context.options.verbose:
		print2(strp)
	purgelog(context,strp)

	
	if 0:
		for flt in filters:
			if flt.walked == 0 and not flt.abstract:
				purgelog(context, "find unwalked filter " + str(flt))
				WalkFiltering(flt.rootdir,filters=[flt])
#pprint.pprint (result)

def loadfilterConf(path):
	if path:
		jsonconf = bibutils.getObjectFromJson(path)
		conf=bibutils.dict2obj(jsonconf)
		return conf
	return None



def startCmd(args):
	global g_starttime
	desc="""
	Ce programme python permet de réaliser une série de purge définie dans le fichier cfgfile spécifié, tout en suivant le standard EIFFAGE
	"""
	parser = OptionParser("%prog -h pour afficher l'aide",description=desc)

	parser.add_option("-x", "--execaction", dest="execaction",  action="store_true",default=False,
					help="exécute les actions de purge, sans ses cette option aucune ation n'est réllement exécutée")

	parser.add_option("-c", "--cfgfile", dest="cfgfile",
					help="Permet de passer le chemin complet du fichier de configuration json contenant les filtres à appliquer",metavar='<path>')

	parser.add_option("-l", "--logfile", dest="logfile",
					help="fichier simple de logs ( utiliser plutôt la variable d'environnement BIB_LOGCONF_PATH)",metavar='<file>')

	parser.add_option("-p", "--printactions", dest="printactions",  action="store_true",default=False,
					help=" affiche sur stdout (par defaut) les actions , préciser --printfile pour envoyer dans un fichier")

	parser.add_option("-q", "--quiet", dest="quiet",  action="store_true",default=False,
					help="n'affiche pas les info de purge à l'écran")

	parser.add_option("-d", "--debug", dest="verbose",  action="store_true",default=False,
					help="affiche les info des process de purge à l'écran")

	parser.add_option("-w", "--debug_walk", dest="debug_walk",  action="store_true",default=False,
					help="affiche les info des process de purge à l'écran")

	parser.add_option("-v", "--version", dest="version",  action="store_true",default=False,
					help="affiche la version du programme de purge")
		
	parser.add_option("-o", "--actionsfile", dest="actionsfile",
					help="fichier pour afficher les résultat de la commande print, stdout par defaut",metavar='<file>')

	
	parser.add_option("-T", "--nbtreads", dest="nbtreads",
					help="nombre de threads en parallele",metavar='<nbtreads>')

	parser.add_option("-L", "--logconffile", dest="logconffile",
						help="fichier précisant tous les paramètres pour les logs ( utiliser plutôt la variable d'environnement BIB_LOGCONF_PATH)",metavar='<file>')

	(g_context.options, args) = parser.parse_args()
	
	if g_context.options.verbose:
		print2("prog purgeman version *** :"+_PURGEMAN_VERSION_)

	if g_context.options.version:
		print ("options:"+str(g_context.options))
	if hasattr(g_context.options,'help'):
		print ("options.help TRUE")
		
	if g_context.options.version:
		import socket
		#import platform
		hostname = socket.gethostname()
		#print platform.uname()
		cmd="iroger maj objet=refversobj,nmobjet=purgeman,nmhost="+hostname.lower()+",novers="+_PURGEMAN_VERSION_
		print ("\n###\ncalling cmd : ",cmd)
		p = subprocess.Popen(cmd, 
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,cwd=os.getcwd())
		while True:
				line = p.stdout.readline()
				if not line:
					break
				print ("IROGER:"+str(line))
		print ("Version : "+str(_PURGEMAN_VERSION_))
		sys.exit( -1)
	
	if g_context.options.cfgfile is None:
		print ("## option --cfgfile introuvable, essayer -h pour afficher l'aide")
		sys.exit( -1)
	
	conf = loadfilterConf(g_context.options.cfgfile)
	
	if not "purgeId" in conf or not  "hostId" in conf :
		print ("#### FATAL ERROR : ###\n\tpurge conf doit definir les clefs purgeId et hostId !!!\n")
		sys.exit( -1)

	
	
		
	if g_context.options.verbose:
		print2("Python purger start...")
	startPurge(conf,g_context)


if __name__ == "__main__":
	startCmd(sys.argv)
	
