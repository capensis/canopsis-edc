#!/usr/bin/env python

# System Libs
import sys
import os

# We define our vars
global base
base = os.environ['EDC_HOME']
global resource_dir
resource_dir = os.environ['EDC_HOME'] + "/cfg"
global log_dir
log_dir = os.environ['EDC_LOG'] 

# We import our libs
from os import listdir
from os.path import isfile, join
import errno
import re
from xml.dom import minidom
from copy import deepcopy
import simplejson as json
import urllib2
import ConfigParser
import unicodedata

# Lib for Messages
from app.Message import Message

# Conf Message
global message
message = Message( log_dir )

import collections

def updateRec(d, u, depth=-1):
    """
    Recursively merge or update dict-like objects. 
    >>> update({'k1': {'k2': 2}}, {'k1': {'k2': {'k3': 3}}, 'k4': 4})
    {'k1': {'k2': {'k3': 3}}, 'k4': 4}
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping) and not depth == 0:
            r = updateRec(d.get(k, {}), v, depth=max(depth - 1, -1))
            d[k] = r
        elif isinstance(d, collections.Mapping):
            d[k] = u[k]
        else:
            d = {k: u[k]}
    return d

def updateMulti(orig_dict, new_dict):
    for key, val in new_dict.iteritems():
        if isinstance(val, collections.Mapping):
            tmp = updateMulti(orig_dict.get(key, { }), val)
            orig_dict[key] = tmp
        elif isinstance(val, (list, long)):
            orig_dict[key] = (orig_dict[key] + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict

def combine(a, b):
        '''recursively merges dict's. not just simple a['key'] = b['key'], if
           both a and bhave a key who's value is a dict then dict_merge is called
           on both values and the result stored in the returned dictionary.'''
        if not isinstance(b, dict):
                return b
        result = deepcopy(a)
        for k, v in b.iteritems():
                if k in result and isinstance(result[k], dict):
                        result[k] = combine(result[k], v)
                else:
                        result[k] = deepcopy(v)
        return result

# Allow a control in the program launch
def getAllExtDataType( ) :
        """
        We get all the type we may have, return an array with all type available
        """
        result          =       []
        classdir        =       "%s/lib/app/" % ( base )
        for f in listdir( classdir ):
                if isfile( join( classdir, f) ) and re.search("^.+\.py$", f ) and f[:-3] != 'Base' and f[:-3] != '__init__' and f[:-3] != 'Error':
                        result.append(f[:-3].lower() )

        return result

def getConfig(file):
	message.addMessage( "ETC_STEP_MESSAGE",  "Order receveid to deal with %s file" % file )
	try:
	        Config = ConfigParser.ConfigParser()
		Config.optionxform=str
        	Config.read(file)
	        return Config
        except Exception as e:
                message.addError('ETC_ERR_FILE_OPERATION', "read", file , e)
                return False

def ConfigSectionMap(section,Config):
        tmp             =       {}
        options         =       Config.options(section)
        for option in options:
                try:
                        tmp[option]     =       Config.get(section, option, False)
                except:
                        tmp[option]     =       None
        return tmp

def getConfigDatabase(file=False):
        conf    =       file.split('.')
        if len(conf)==2:
                try:
			file_to_get	=	"%s/db/%s.cfg" % (resource_dir, conf[0])
                        Config          =       getConfig(file_to_get)
                except:
			message.addError('ETC_ERR_CONFIG', "Cannot retrieve Database configuration file '%s'" % file , 2 )
                        return False
                try:
                        sections        =       Config.sections()
                        if conf[1] in sections:

                                arr_keys_required       =       ['dbtype','host','user','password','sid']
                                arr_keys_optional       =       ['crypted','port']
                                config                  =       {}

                                for key in arr_keys_required:
                                        try:
                                                config[key]     =       ConfigSectionMap(conf[1],Config)[key]
                                        except Exception as e:
						message.addError('ETC_ERR_CONFIG', "Required key '%s' not in Database configuration '%s' : %s" % (key,file,e) , 2 )
                                                return False
                                for key in arr_keys_optional:
                                        try:
                                                config[key]     =       ConfigSectionMap(conf[1],Config)[key]
                                        except:
						pass
				return config
                        else:
				message.addError('ETC_ERR_CONFIG', "Section '%s' not in Database configuration '%s'" % (conf[1],conf[0]) , 2 )
                                return False
                except Exception as e:
			message.addError('ETC_ERR_CONFIG', "Cannot retrieve Section '%s' of Database configuration '%s' : %s" % (conf[1],conf[0],e) , 2 )
                        return False
        else:
		message.addError('ETC_ERR_CONFIG', "Cannot retrieve Database configuration file '%s'" % file , 2 )
                return False


def updateMapping(mapping,key,val,config):
        available_mapping_fct   =       ['copy','constant']
        available_mapping_fct2  =       ['concat','substring']
	chain   =       key.split('.')
        try:
        	if len(chain) and (chain[-1] in available_mapping_fct or (len(chain)>=2 and chain[-2] and chain[-2] in available_mapping_fct2)):
                	if chain[-1] == 'copy':
                        	del chain[-1]
                                mapping['fields_renaming']['.'.join(chain)]        =       [val,True,True]
                        elif chain[-1] == 'constant':
                        	del chain[-1]
                                mapping['records_constants']['.'.join(chain)]    =       val
                        elif len(chain)>=2 and chain[-2] and chain[-2] == 'concat':
                        	add_dv  =       False
                                if chain[-1] == 'source':
                                        chain2          =       chain
                                        del chain2[-1]
                                        delim_dv       =       '.'.join(chain2) + '.delimiter'
                                        dv_fields       =       val.split(',')
                                        if delim_dv in config.keys():
	                                        try:
        	                                        delimiter       =       config[delim_dv][1:-1]
                                                        add_dv  =       True
                                                except Exception as e:
                                                        message.addError('ETC_ERR_CONFIG', e , 2 )
                                        else:
                                                message.addError('ETC_ERR_CONFIG', "Missing parameters for the dynamic value '%s' concatenation" % (chain2[0]) , 2 )
                                        if add_dv:
                                                dv      =       { "function" : { "name": "concat", "delimiter" : delimiter, "fields_values": dv_fields } }
                                                del chain[-1]
                                                mapping['dynamic_values']['.'.join(chain)]    =       dv

                        elif len(chain)>=2 and chain[-2] and chain[-2] == 'substring':
                                add_dv  =       False
                                if chain[-1] == 'source':
                                        chain2          =       chain
                                        del chain2[-1]
                                        start_dv       =       '.'.join(chain2) + '.start'
					end_dv		=	'.'.join(chain2) + '.end'
					length_dv	=	'.'.join(chain2) + '.length'
                                        delimiter       =       val
                                        if start_dv in config.keys() or end_dv in config.keys() or length_dv in config.keys():
                                                try:
							start	=	False
							end	=	False
							length	=	False
							if start_dv in config.keys():
								start	=	config[start_dv]
                                                        if end_dv in config.keys():
                                                                end	=       config[end_dv]
                                                        if length_dv in config.keys():
                                                                length	=       config[length_dv]
							del chain[-1]
	                                                dv      =       { "function" : { "name": "substring", "start" : start, "end": end, "length": length, "source": val } }
                	                                mapping['dynamic_values']['.'.join(chain)]    =       dv

                                                except Exception as e:
                                                        message.addError('ETC_ERR_CONFIG', e , 2 )
                                        else:
                                                message.addError('ETC_ERR_CONFIG', "Missing parameters for the dynamic value '%s' concatenation" % (chain2[0]) , 2 )
		return mapping
	except Exception as e:
        	message.addError('ETC_ERR_CONFIG', e , 2 )
		return mapping
	return mapping

def getSourceConfigurationToArray(file=False,name=False):
	try:
		list_types	=	getAllExtDataType()
	except :
		list_types	=	False
        cfg             	=       {}
	available_mapping_fct	=	['copy','constant']
	available_mapping_fct2  =       ['concat']
        if file and list_types:
                try:
                        Config          =       getConfig(file)
                except Exception as e:
			message.addError('ETC_ERR_CONFIG', "impossible to retrieve the source configuration (%s). verify the file" %  file , 2 )
                        return False
                try:
                        sections        =       Config.sections()
			try:
				type	=	ConfigSectionMap('general',Config)['type'].lower()
			except:
				type	=	False
                        try:
                                template    =       ConfigSectionMap('general',Config)['template'].lower()
                        except:
                                template    =       False

                        if 'general' in sections and type and type in list_types:
				try:
					for section in sections:
						if section == 'general':
                                                        tmp     =       ConfigSectionMap(section,Config)
                                                        for key, val in tmp.iteritems():
                                                                if name not in list_types and type and ( template==False or template.lower()=='false'):

                                                                        parent_url      =       "%s/datasrc/common/_%s.cfg" % (resource_dir,type)
                                                                        parent          =       getSourceConfigurationToArray(file=parent_url,name=type)
                                                                        if parent:
										cfg     =       updateRec(cfg,parent)

                                                                elif key == 'template' and val and val!='False':
                                                                        tmpurl          =       val.split('.')
                                                                        parent_url      =       "%s/datasrc/%s.cfg" % (resource_dir,val)
                                                                        if len(tmpurl) > 1:
                                                                                parent_url      =       "%s/datasrc/%s.cfg" % (resource_dir,'/'.join(tmpurl))
                                                                        parent          =       getSourceConfigurationToArray(file=parent_url,name=type)
                                                                        if parent:
										cfg	=	updateRec(cfg,parent)
	                                for section in sections:
        	                                if section == 'mapping':
                	                                tmp    	=       ConfigSectionMap(section,Config)
							if cfg.has_key('mapping'):
								mapping	=	cfg['mapping']
							else:
								mapping	=	{}
								mapping['fields_renaming']	=	{}
								mapping['records_constants']	=	{}
								mapping['dynamic_values']	=	{}
								mapping['delete_fields']	=	[]
                                                        for key, val in tmp.iteritems():
								if key == 'deletefields':
									xxx				=	val.split(',')
									for x in xxx:
										if x != 'False':
											mapping['delete_fields'].append(x)
									
							for key, val in tmp.iteritems():
								mapping	=	updateMapping(mapping,key,val,tmp)
							cfg['mapping']	=	mapping

                                	        elif section == 'general':
                                        	        tmp     =       ConfigSectionMap(section,Config)
							for key, val in tmp.iteritems():
								if val:
									cfg[key]	=	val

				except Exception as e:
					message.addError('ETC_ERR_CONFIG', e , 2 )

				return cfg
                        else:
				message.addError('ETC_ERR_CONFIG', "Missing section 'general' in the source configuration (%s). verify the file" %  file , 2 )
                                return False
                except:
			message.addError('ETC_ERR_CONFIG', "Impossible to retrieve the data in the source configuration (%s). verify the file" %  file , 2 )
                        return False
        else:
		message.addError('ETC_ERR_CONFIG', "Configuration file (%s) non compatible. verify the file" %  file , 2 )
                return False
        return False

def getCallbackConfigurationToArray(file=False, fct=False):
        cfg             =       {}
        if file and fct:
                try:
                        Config          =       getConfig(file)
                except Exception as e:
                        message.addError('ETC_ERR_CONFIG', "impossible to retrieve the source configuration (%s). verify the file" %  file , 2 )
                        return False
                try:
                        sections        =       Config.sections()
                        if fct in sections:
                                try:
                                        tmp     =       ConfigSectionMap(fct,Config)
                                        for key, val in tmp.iteritems():
                                        	cfg[key]        =       val
                                except Exception as e:
                                        message.addError('ETC_ERR_CONFIG', e , 2 )
					return False

                                return cfg
                        else:
                                message.addError('ETC_ERR_CONFIG', "Missing section '%s' in the source configuration (%s). verify the file" %  (fct,file) , 2 )
                                return False
                except:
                        message.addError('ETC_ERR_CONFIG', "Impossible to retrieve the data in the source configuration (%s). verify the file" %  file , 2 )
                        return False
        else:
                message.addError('ETC_ERR_CONFIG', "Configuration file (%s) non compatible. verify the file" %  file , 2 )
                return False
        return False



def getConfigurationToArray(file=False):
	cfg		=	{}
	tplcfg		=	{}
	sources		=	[]
	sources_cfg	=	[]
	callbacks	=	[]
	callback_list	=	[]
	callback_cfg    =       []
        srccallbacks    =       []
        srccallback_list=       []
        srccallback_cfg =       []
	src_pt		=	{}
	general_keys	=	['name','description','refresh']

	tmpfile		=	file.split('.')
	source_file     =       "%s/cfg/exec_src/%s.cfg" % (base,file)
	if len(tmpfile) > 1:
		source_file     =       "%s/cfg/exec_src/%s.cfg" % (base,'/'.join(tmpfile))

        if file:
                try:
                        Config          =       getConfig(source_file)
                except:
			message.addError('ETC_ERR_CONFIG', "impossible to retrieve the source configuration (%s). verify the file" %  file , 2 )
                        return False
                try:
                        sections        =       Config.sections()
                        if 'general' in sections:
				for section in sections:
					if section == 'general':
                                                tmp     =       ConfigSectionMap(section,Config)
                                                try:
                                                        for key, val in tmp.iteritems():
                                                                if key == 'template' and val!='False' and val:
                                                                        tplcfg       =       getConfigurationToArray(val)
                                                                        break
                                                except Exception as e:
                                                        message.addError('ETC_ERR_CONFIG', e , 2 )

                       		for section in sections:
					if section == 'output':
						cfg[section]	=	ConfigSectionMap(section,Config)
					elif section == 'general':
						tmp	=	ConfigSectionMap(section,Config)
						for key, val in tmp.iteritems():
							if key in general_keys:
								cfg[key]	=	val
							elif key == 'use':
								tmp	=	val.split(',')
								for datasource in tmp:
									try:
										tmpdatasrc	=	datasource.split('.')
										namedatasrc	=	tmpdatasrc[-1]
										rootdatasrc	=	''
										if len(tmpdatasrc) > 1:
											tmpdatasrc.pop(-1)
											rootdatasrc	=	'/'.join(tmpdatasrc)+"/"
										urldatasrc	=	rootdatasrc + namedatasrc
									except Exception as e:
										urldatasrc	=	datasource
										message.addError('ETC_ERR_CONFIG', e , 2 )
									tmpurl		=	urldatasrc.split('.')
									sourcecfg	=	"%s/datasrc/%s.cfg" % (resource_dir,urldatasrc)
									if len(tmpurl)>1:
										sourcecfg       =       "%s/datasrc/%s.cfg" % (resource_dir,'/'.join(tmpurl))
									if os.path.exists(sourcecfg):
										sources.append(datasource)
										sourceconfig       =       getSourceConfigurationToArray(sourcecfg)
										if sourceconfig:
											sourceconfig['name']	=	datasource
											sources_cfg.append(sourceconfig)
									else:
										message.addError('ETC_ERR_CONFIG', "Source file '%s' does not exist, source not loaded" % sourcecfg , 2 )

							elif key == 'callbacks':
								try:
	                                                                callbacklist     =       val.split(',')
									if len(callbacklist):
	        	                                                        for callback in callbacklist:
											if callback and callback != 'False':
			                                                                        try:
        	        		                                                                tmpcb		=       callback.split('.')
                	                		                                                cbfct     	=       tmpcb[-1]
													cbfile		=	tmpcb[-2]
                                	                		                                rootcb     	=       ''
                                        	                        		                if len(tmpcb) > 2:
                                                	                                		        tmpcb.pop(-1)
														tmpcb.pop(-1)
		                                                	                                        rootcb	=       '/'.join(tmpcb)+"/"
                		                                        	                        urlcb      	=       rootcb + cbfile
                                		                                	        except Exception as e:
													urlcb		=	callback
                                                                		                	message.addError('ETC_ERR_CONFIG', e , 2 )

	                                                                                        callbackcfg     =       "%s/proc/%s.cfg" % (resource_dir,urlcb)
        	                                                                                callbackpy      =       "%s/lib/proc/%s.py" % (base,urlcb)
												tmpurl          =       urlcb.split('.')
												if len(tmpurl)>1:
													callbackcfg     =       "%s/proc/%s.cfg" % (resource_dir,'/'.join(tmpurl))
													callbackpy      =       "%s/lib/proc/%s.py" % (base,'/'.join(tmpurl))
        	                        		                                        if os.path.exists(callbackcfg) and os.path.exists(callbackpy):
													try:
	                	                        		                                        callbacks.append(callback)
        	                	                        		                                callbackconfig       =       getCallbackConfigurationToArray(callbackcfg, cbfct)
														tmppt	=	{}
														if callbackconfig:
															tmppt[callback]	=	callbackconfig
														else:
															tmppt[callback]  =       {}
														callback_cfg.append(tmppt)
													except Exception as e:
														message.addError('ETC_ERR_CONFIG', e , 2 )
                                                                        			elif urlcb !='False':
													message.addError('ETC_ERR_CONFIG', "Either callback file '%s' or '%s'  does not exist, source not loaded" % (callbackcfg,callbackpy) , 2 )
								except Exception as e:
									message.addError('ETC_ERR_CONFIG', e , 2 )
                                                        elif key == 'source_callbacks':
                                                                try:
                                                                        srccallbacklist     =       val.split(',')
                                                                        if len(srccallbacklist):
                                                                                for callback in srccallbacklist:
                                                                                        if callback and callback != 'False':
												nmfct	=	False
                                                                                                try:
													for src in sources:
														if callback[:len(src)] == src:
															callback	=	callback[len(src)+1:]
		                                                                                                        tmpcb           =       callback.split('.')
                		                                                                                        cbfct           =       tmpcb[-1]
                                		                                                                        cbfile          =       tmpcb[-2]
                                                		                                                        rootcb          =       ''
                                                                		                                        if len(tmpcb) > 2:
                                                                                		                                tmpcb.pop(-1)
                                                                                                		                tmpcb.pop(-1)
                                                                                                                		rootcb  =       '/'.join(tmpcb)+"/"
		                                                                                                        urlcb           =       rootcb + cbfile
															break
                                                                                                except Exception as e:
                                                                                                        urlcb           =       callback
                                                                                                        message.addError('ETC_ERR_CONFIG', e , 2 )

                                                                                                callbackcfg     =       "%s/proc/%s.cfg" % (resource_dir,urlcb)
                                                                                                callbackpy      =       "%s/lib/proc/%s.py" % (base,urlcb)
                                                                                                tmpurl          =       urlcb.split('.')
                                                                                                if len(tmpurl)>1:
                                                                                                        callbackcfg     =       "%s/proc/%s.cfg" % (resource_dir,'/'.join(tmpurl))
                                                                                                        callbackpy      =       "%s/lib/proc/%s.py" % (base,'/'.join(tmpurl))
                                                                                                if os.path.exists(callbackcfg) and os.path.exists(callbackpy):
                                                                                                        try:
                                                                                                                srccallbacks.append(callback)
                                                                                                                callbackconfig       =       getCallbackConfigurationToArray(callbackcfg, cbfct)
                                                                                                                tmppt   =       {}
                                                                                                                if callbackconfig:
                                                                                                                        tmppt[callback] =       callbackconfig
                                                                                                                else:
                                                                                                                        tmppt[callback]  =       {}
                                                                                                                srccallback_cfg.append(tmppt)

						                                                                if src_pt.has_key(src) == False:
                                                						                        src_pt[src]     	=       {}
                                                						                src_pt[src]       =       tmppt

                                                                                                        except Exception as e:
                                                                                                                message.addError('ETC_ERR_CONFIG', e , 2 )
                                                                                                elif urlcb !='False':
                                                                                                        message.addError('ETC_ERR_CONFIG', "Either callback file '%s' or '%s'  does not exist, source not loaded" % (callbackcfg,callbackpy) , 2 )
                                                                except Exception as e:
                                                                        message.addError('ETC_ERR_CONFIG', e , 2 )

							elif key != 'template' and key!='source_callbacks':
								message.addMessage( "ETC_STEP_MESSAGE",  "'%s' is not supposed to be in the general section of the config file" % key )
				for section in sections:
					tmp	=	section.split('.')
					if len(tmp)>1 and '.'.join(tmp[:-1]) in sources:
						i	=	-1
						for ds in sources_cfg:
							i	+=	1
							if ds.has_key('name') and ds['name'] == '.'.join(tmp[:-1]):
								newconfig	=	ConfigSectionMap(section,Config)
								if tmp[-1] == 'mapping':
        	        	                                        newmapping =       sources_cfg[i]['mapping']
									sources_cfg[i].pop('mapping')
		                                                        for key, val in newconfig.iteritems():
                		                                                if key == 'deletefields':
                                		                                        xxx                             =       val.split(',')
                                                		                        for x in xxx:
                                                                		                if x != 'False' and x not in newmapping['delete_fields']:
                                                                                		        newmapping['delete_fields'].append(x)

		                                                        for key, val in newconfig.iteritems():
                		                                                newmapping =       updateMapping(newmapping,key,val,newconfig)
                                		                        sources_cfg[i]['mapping']	=	newmapping
								elif tmp[-1] == 'general':
									for a,b in newconfig.iteritems():
										if ds.has_key(a) and b:
											ds[a]	=	b
									sources_cfg[i]	=	ds
								elif section in callbacks:
									tmppt   =       {}
                                                                        for a,b in newconfig.iteritems():
                                                                                tmppt[a]   =       b

									i	=	0
									for cb in callback_cfg:
										if cb.has_key(section):
											callback_cfg[i][section].update(tmppt)
											break
										i	+=	1
									
								else:
									message.addError('ETC_ERR_CONFIG', "Cannot interpret what is configured with '%s'" % section , 2 )
					elif len(tmp)>1 and section in callbacks:
						newconfig       =       ConfigSectionMap(section,Config)
						i	=	-1
						for cb_cfg in callback_cfg:
							i	+=	1
							if section in cb_cfg.keys():
								cbnew   =       cb_cfg[section]
                                                        	for a,b in newconfig.iteritems():
                                                                	if b:
                                                                        	cbnew[a]   =       b
                                                                callback_cfg[i]  =       { section : cbnew }
					
					elif section not in ['output','general']:
						cmpt	=	0
						for src in sources:
							if section[0:len(src)] == src:
								if src_pt.has_key(src) == False:
									src_pt[src]	=	{}
								newconfig       =       ConfigSectionMap(section,Config)
								src_pt[src][section[len(src)+1:]].update(newconfig)
								cmpt	+=	1
						if cmpt == 0:
							message.addError('ETC_ERR_CONFIG', "Cannot interpret what is configured with '%s'" % section , 2 )
			
				cfg['data_sources']	=	sources_cfg
				cfg['post_treatments']	=	callback_cfg
				cfg['src_pt']		=	src_pt

				if len(tplcfg):
					cfg	=	updateMulti(tplcfg,cfg)

				return cfg
                        else:
				message.addError('ETC_ERR_CONFIG', "Missing section 'general' in the source configuration (%s). verify the file" %  file , 2 )
                                return False
                except Exception as e:
			message.addError('ETC_ERR_CONFIG', "Impossible to retrieve the data in the source configuration (%s). verify the file : %s" %  (file,e) , 2 )
                        return False
        else:
		message.addError('ETC_ERR_CONFIG', "Configuration file (%s) non compatible. verify the file" %  file , 2 )
                return False
	return False


def getConfigurationMultiToArray(file=False):	
        tmpfile         =       file.split('.')
        source_file     =       "%s/cfg/multi/%s.cfg" % (base,file)
        if len(tmpfile) > 1:
                source_file     =       "%s/cfg/multi/%s.cfg" % (base,'/'.join(tmpfile))
	results		=	[]
        if file:
                try:
                        Config          =       getConfig(source_file)
                        sections        =       Config.sections()
                        for section in sections:
				sect	=	section.strip()
		                results.append( {sect : ConfigSectionMap(section,Config) } )
                except Exception as e:
                        message.addError('ETC_ERR_CONFIG', "impossible to retrieve the source configuration (%s). verify the file : %s" %  (file , e) )
                        return False
	return results


# Write content in file
def writeInFile(data,filename):
	"""
	Retrieve data to write in a file
	"""
	try:
        	with open(filename, 'w') as cacheFile:
                	cacheFile.write(data)
		return True
        except Exception as e:
                message.addError('ETC_ERR_FILE_OPERATION', "write", filename , e)
		return False

# Retrieve a JSON file and return a formatted array
def getJsonToArray(file=False,string=False):
        """
        Convert JSON File to Python Array
        """
	data = None
	if file:
        	# We store the content of the JSON in the variable f
		try:
		        f = open(file,'r').read()
       		 	try:
	        	# We transform the JSON into a library
        	        	data = json.loads(f)
		        except Exception as e:
        		        message.addError( "ETC_ERR_LIBRARY", "simplejson" , e)
                		return False
		except Exception as e:
			message.addError('ETC_ERR_FILE_OPERATION',"read",  file  , e)
			return False
	elif string:
		try:
			data = json.loads(string)
                except Exception as e:
                        message.addError( "ETC_ERR_LIBRARY", "simplejson", e)
                        return False

        return data

# Retrieve file using proxy
def getDynamicFile(url,proxy=False):
	"""
	Open a distant file w/ or w/o Proxy settings
	"""
	headers={'User-agent' : 'Mozilla/5.0'}
	if proxy:
		proxies = {}
		for method,prox in proxy.iteritems():
			if url.startswith('http')==False:
				proxies[method] = "%s://%s" % (method,prox)
			else:
				proxies[method] = prox
		proxy_support = urllib2.ProxyHandler(proxies)
		opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler(debuglevel=1))
		urllib2.install_opener(opener)
	req	=	urllib2.Request(url, None, headers)
	html	=	False
	try:
		file	=	urllib2.urlopen(req, timeout=1)
		html	=	file.read()
	except Exception as e:
		message.addError( "ETC_ERR_LIBRARY", "urllib2", e)
	return html

# Retrieve file content
def getFileContent(url,encode=False,proxy=False):
	"""
	Returns the content of a file and tries to return it as unicode
	"""
	if proxy==False and url.startswith('http')==False:
		content = open(url,'r').read()
	else:
		content = getDynamicFile(url,proxy)
	if encode:
		try:
			content.decode(encode)
		except:
			pass
	else:
		try:
	        	tmp_content = try_unicode(content,'strict')
		        if tmp_content:
        		        content = tmp_content
		except:
			pass
	return content

# Converts onto Unicode
def try_unicode(string, errors='strict'):
	"""
	Tries to convert a string into unicode
	"""
	encoding_guess_list = ["utf-8","ascii","cp1250", "latin1", "iso-8859-2","iso-8859-1","utf-16"]
	if isinstance(string, unicode):
		return string
	assert isinstance(string, str), repr(string)
	for enc in encoding_guess_list:
		try:
			return string.decode(enc, errors)
		except UnicodeError, exc:
			continue

# Converts Dict into XML Element
def dict2element(root,structure,doc,elt_val):
	"""
	Gets a dictionary like structure and converts its
	content into xml elements. After that appends
	resulted elements to root element. If root element
	is a string object creates a new elements with the
	given string and use that element as root.

	This function returns a xml element object.

	"""
    	# if root is a string make it a element
	if isinstance(root,str):
        	root = doc.createElement(root)
    	if isinstance(structure, list):
		for tmp in structure:
			parent = doc.createElement(elt_val)
                	for key,value in tmp.iteritems():
                        	el = doc.createElement(str(key))
	                        if isinstance(value, (dict,tuple)):
        		                dict2element(el,value,doc,elt_val)
                	        else:
                                        el.appendChild(doc.createCDATASection(str(value) if value is not None  else ''))
                                	parent.appendChild(el)
			root.appendChild(parent)

    	else:
        	for key,value in structure.iteritems():
                	el = doc.createElement(str(key))
                	if isinstance(value, (dict,tuple)):
	                    	dict2element(el,value,doc,elt_val)
                	else:
        	            	el.appendChild(doc.createTextNode(str(value) if value is not None  else ''))
                		root.appendChild(el)
    	return root

# Converts Dict into XML
def dict2xml(structure,tostring=False,elt_val='element'):
    	"""
    	Gets a dict like object as a structure and returns a corresponding minidom
    	document object.

    	If str is needed instead of minidom, tostring parameter can be used

    	Restrictions:
    	Structure must only have one root.
    	Structure must consist of str or dict objects (other types will
    	converted into string)

    	Sample structure object would be
    	{'root':{'elementwithtextnode':'text content','innerelements':{'innerinnerelements':'inner element content'}}}
    	result for this structure would be
    	'<?xml version="1.0" ?>
    	<root>
      		<innerelements><innerinnerelements>inner element content</innerinnerelements></innerelements>
      	<elementwithtextnode>text content</elementwithtextnode>
    	</root>'
    	"""
    	# This is main function call. which will return a document
    	assert len(structure) == 1, 'Structure must have only one root element'

    	root_element_name, value = next(structure.iteritems())
    	impl = minidom.getDOMImplementation()
    	doc = impl.createDocument(None,str(root_element_name),None)
    	dict2element(doc.documentElement,value,doc,elt_val)
	return doc.toxml() if tostring else doc

# Verify path existency
def make_sure_path_exists(path):
    	"""
    	Check if dir exist and if not creates it
    	"""
    	try:
        	os.makedirs(path)
    	except OSError as exception:
        	if exception.errno != errno.EEXIST:
            		raise

# Merge two dicts
def combine(a, b):
        """
	recursively merges dict's. not just simple a['key'] = b['key'], if
           both a and bhave a key who's value is a dict then dict_merge is called
           on both values and the result stored in the returned dictionary.
	"""
        if not isinstance(b, dict):
                return b
        result = deepcopy(a)
        for k, v in b.iteritems():
                if k in result and isinstance(result[k], dict):
                        result[k] = combine(result[k], v)
                else:
                        result[k] = deepcopy(v)
        return result

# Retrieve timestamp from connector files
def getTimestampFile(file):
	"""
	Retrieve the timestamp included in the file
	Model : filename = source + _ + timestamp
	"""
        filename = file.split('.')
        ts = filename[0].split('_')
	try:
		return int(ts[-1])
	except:
	        return 0

# Check if string ascii
def is_ascii(s):
	"""
	Return boolean on if string is ascii
	"""
	return all(ord(c) < 128 for c in s)

# Converts to the closest ascii string
def remove_accents(input_str):
	"""
	Returns the closest str
	"""
        nkfd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nkfd_form.encode('ASCII', 'ignore')
        return only_ascii

# Recursively encode datas
def dataDecodeEncode(data,decode,encode):
	"""
	Fonction recursive d'encode et decode data
	"""
	if ( isinstance(data, list)):
		table = []
		for elt in data:
			table.append( dataDecodeEncode(elt,decode,encode) )
		return table
	elif ( isinstance( data, dict)):
		new_dict = { }
		for key,val in data.iteritems():
			new_dict[key] = dataDecodeEncode(val,decode,encode)
		return new_dict
	elif ( isinstance ( data, basestring)) :
		if ( is_ascii(data) and decode == 'ascii' ) :
			decode = 'ascii'
			return data.encode(encode)
		else:
			try:
				try:
					return data.decode(decode).encode(encode)
				except:
					return remove_accents(try_unicode(data)).decode(decode).encode(encode)
			except Exception as e2:
				try:
					return data.decode('utf-8', 'ignore').encode(encode)
				except Exception as e:
						message.addError('ETC_ERR_ENCODE',  decode, encode, e2 )
						message.addError('ETC_ERR_ENCODE',  'latin1', encode, e )
	else:
		return data


# End candles.py
