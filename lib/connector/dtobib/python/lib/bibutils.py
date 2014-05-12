# -*- coding: utf-8 -*-
import logging,sys,os
import biblog
import json
import errno

def getObjectFromJson(filename):
	try:
		file_object=open(filename)
	except IOError :
		err = str(sys.exc_info()[1])
		print ("exception:"+err)
		print ("\nERR_DB_CFG_FILE_NOT_FOUND:  vérifier que le fichier de conf de log fourni '"+filename+"' existe vraiment ")
		exit(1)
	try:
		newobject = json.loads(file_object.read())
	except IOError :
		err = str(sys.exc_info()[1])
		print ("exception:"+err)
		print ("v�rifier l'erreur de syntaxe dans le fichier")
		return None
	return newobject

def getJsonFromObject(obj):
	return json.dumps(obj)

class dict2obj(dict):
	def __init__(self, dict_,optkeys=None):
		super(dict2obj, self).__init__(dict_)
		for key in self:
			item = self[key]
			if isinstance(item, list):
				for idx, it in enumerate(item):
					if isinstance(it, dict):
						item[idx] = dict2obj(it)
			elif isinstance(item, dict):
				self[key] = dict2obj(item)
		if optkeys:
			for k in optkeys :
				if k not in self:
					self[k] = "?"+k
	def __getattr__(self, key):
		return self[key]

is_array = lambda var: isinstance(var, (list, tuple))

	
def array2Dict(arr,prefix=""):
	dic = {}
	dic[prefix+str(0)]=""
	for i,v in enumerate(arr):
		dic[prefix+str(i+1)]=v
	return dic

def getSimpleConfig():
	import SimpleConfigParser
	filename = 'debug.ini'
	cp = SimpleConfigParser.SimpleConfigParser()
	cp.read(filename)
	print ('getoptionslist():', cp.getoptionslist())
	for option in cp.getoptionslist():
		print ("getoption('%s') = '%s'" % (option, cp.getoption(option)))
		print ("hasoption('wrongname') =", cp.hasoption('wrongname'))
		
def readConfig(filename='example.cfg'):
	import ConfigParser
	config = ConfigParser.RawConfigParser()
	config.read(filename)
	return config



def createdir(errfile):
	path=os.path.dirname(errfile)
	if len(path)==0:
		return
	try:
		os.makedirs(path)
	except OSError :
		etype = str(sys.exc_info()[0])
