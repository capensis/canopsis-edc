#!/usr/bin/env python

# System Libs
import sys
import os
from time import sleep

# We define our vars
global base
base = os.environ['EDC_HOME']
global cache_dir
cache_dir = os.environ['EDC_VAR'] + "/cache" 
global run_dir
run_dir = os.environ['EDC_VAR'] + "/run"
global resource_dir
resource_dir = os.environ['EDC_HOME'] + "/cfg"
global log_dir
log_dir = os.environ['EDC_LOG'] 

# General Libs
try:
	import simplejson as json
except:
	import json

from os import listdir
from os.path import isfile, join
from os import environ
import re
import glob
import types
import inspect
import time

# Export CSV
import csv

# Lib for Messages
from app.Message import Message
global message
message = Message( log_dir )

# Export XML
from xml.dom import minidom

# Other dev
import candles

# Sometimes types are not hashable, so we for dumps purposes we try to convert them in string
def jsonDumpsFail(data):
	try:
        	newdata =       {}
                for ds, list in data.iteritems():
                	newdata[ds]     =       list
                        if 'data' in list.keys():
                        	newresult       =       []
                                for row in list['data']:
                                	newline =       {}
                                        for key, value in row.iteritems():
                                        	try:
                                                	newline[key]    =       str(value)
                                                except:
                                                	newline[key]    =       value
                                                newresult.append(newline)
                	newdata[ds]['data']     =       newresult
                return newdata
	except Exception as e:
        	return data


# Called for callbacks and dumps
def dataOutput(data,output,source):
	"""
	Format the results into required output
	"""
	if data:
		"""
		INIT
		"""
		if output and output.has_key('type'):
			type = output['type']
		else:
			type = 'JSON'

		if output and output.has_key('encoding'):
			encoding = output['encoding']
		else:
			encoding = 'utf-8'
		# Function who decodes first then encode
		data = candles.dataDecodeEncode(data, 'ascii', encoding)

		"""
		TREATMENTS
		"""
		# Returns Python dict
		if type == 'Python':
			return data
		# Dumps the Python dict
                elif type == 'JSON' :
                        try:
                                return json.dumps(data, use_decimal=True, indent=4)
                        except Exception as e:
				try:
					newdata	=	jsonDumpsFail(data)
					return json.dumps(newdata, use_decimal=True, indent=4)
				except:	
	                                message.addError("ETC_ERR_LIBRARY", "simplejson", e)
        	                        return False
		# Creates a file per source (cf. config) and returns the directory path
		elif type in ['CSV','XML','SQL']:
			directory = "%s/dmp/%s" % (cache_dir,source)
			candles.make_sure_path_exists(directory)
			dir_files = []
			if True:
				cmpt_filename = {}
				for query_name, line in data.items():
					if line.has_key('data'):
						line_data = line['data']
						# We determine the filename of the output - 1 output per query
						filename = "%s/%s.%s" % (directory,query_name,type.lower())
						# We already have a filename similar for another query
						if filename in dir_files:
							if cmpt_filename.has_key(query_name) == False:
								cmpt_filename[query_name] = 0
							cmpt_filename[query_name] += 1
							filename = "%s/%s_%d.%s" % (directory,query_name,cmpt_filename[query_name],type.lower())
						else:
							dir_files.append(filename)
						
						# Output is set as csv
						if type == 'CSV':
							# Default value of delimiter
							delimiter_val = ';'
							# If the delimiter is paramed
                                        	        if output.has_key('params') and output['params'].has_key('delimiter'):
                                                	        delimiter_val = output['params']['delimiter']
							# We writer the content in CSV
							try:
								out = csv.writer(open(filename,"w"), delimiter=delimiter_val, quoting=csv.QUOTE_ALL)
								out.writerow(line_data[0].keys())
								for row in line_data:
									out.writerow([str(x) for x in row.values()])
							except Exception as e:
								message.addError("ETC_ERR_LIBRARY", "csv", e )
						# Output is set as xml
						elif type == 'XML':
							# Default value of root tag element
        	                                        root_val = 'root'
							# If paramed
                	                                if output.has_key('params') and output['params'].has_key('root_name'):
                        	                                root_val = output['params']['root_name']
							# Default value of item tag element
                                	                elt_val = 'element'
							# If paramed
                                        	        if output.has_key('params') and output['params'].has_key('line_name'):
                                                	        elt_val = output['params']['line_name']
							# We write the XML in the file
	                                                try:
        	                                                dict            =       {root_val: line_data}
                	                                        result          =       candles.dict2xml(dict,True,elt_val=elt_val)
								candles.writeInFile(result,filename)
                                        	        except Exception as e:
                                                	        message.addError("ETC_ERR_LIBRARY", "xml", e )
						#Output is set as SQL
						elif type == 'SQL':
							# Default value of the table (insert into ***)
        	                                        tablename_val = '__tablename__'
							# If paramed
                	                                if output.has_key('params') and output['params'].has_key('tables'):
								# We parse to match the name of query to the conf data_output
                        	                                for inst,tablename in output['params']['tables'].iteritems():
                                	                                if inst == queryname:
                                        	                                tablename_val = tablename
                                                	                        break
							# We create the query and write it in file
	                                                try:
        	                                                iteration = 0
                	                                        request = ""
                        	                                for elt in line_data:
                                	                                separator = ','
                                        	                        if iteration == 0:
                                                	                        request += "insert into %s (%s) values " % (tablename_val,(','.join(elt.keys())))
                                                        	        if iteration == (len(line_data)-1):
                                                                	        separator = ';'
	                                                                request += '("%s")%s' % ('","'.join([str(x) for x in elt.values()]),separator)
        	                                                        iteration += 1
								# We write the content in the file
								candles.writeInFile(request,filename)
                                        	        except Exception as e:
                                                	        message.addError("ETC_ERR_FORMAT", "Impossible to dump python object as sql",  e )

			# If only one filename we return the path of the file
			if len(data) == 1:
				return filename
			# If several, we return the directory
			else:
				return directory

		else:
			# We try to dump in Json if no other type is found
                        try:
                                return json.dumps(data, use_decimal=True, indent=4)
                        except Exception as e:
                                try:
                                        newdata =       jsonDumpsFail(data)
                                        return json.dumps(newdata, use_decimal=True, indent=4)
                                except:
                                        message.addError("ETC_ERR_LIBRARY", "simplejson", e)
                                        return False

	else:
		return False

# Handles the lock file system and source refreshing according configuration
def processRefresh(source,args=False):
	"""
	handles multi-call of the same sources (one processing the other fifo)
	lauches treatment of the source
	"""	
	message.addMessage( "ETC_STEP_MESSAGE",  "Order receveid to deal with %s source" % source )
	is_lock = False
	
	# We parse all the cache files having the source name
        parse           =       "%s/%s_[0-9]*.lock" % (run_dir,source)
	try:
	        list            =       glob.glob(parse)
	except Exception as e:
		message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to list lock file in %s" % parse, e)
	
	# Timestamp value to use for dumping datas
        ts              =       int(time.time())

	# If we have lock files
	if len(list):
		for lock in list:
			# We force the deletion of lock files
			if (len ( sys.argv ) > 2 and '-f' in sys.argv) or (args and '-f' in args):
 	                       if os.path.isfile(lock):
        	                       # We remove the lock file
                                       os.remove(lock)
			else:
				# We retrieve the timestamp of the lock file
				ts_lock 	= 	candles.getTimestampFile(lock)
				# We don't consider lock files older than an hour
				if (ts - 3600) > ts_lock :
		                	if os.path.isfile(lock):
                	        		# We remove the lock file
	                        		os.remove(lock)
				# If we have a lock file younger than an hour we consider the source running
				else: 
					is_lock = 	True

	# The filename of the current lock file
	curr_lock 	= 	"%s/%s_%s.lock" % (run_dir,source,ts)

	# We create an empty file to tell we are processing the source
	candles.writeInFile("",curr_lock)

        # We init our vars
	ts 		= 	int(time.time())

        # We get the configuration file
	data		=	candles.getConfigurationToArray(file=source)

	# We set that we want to create results from the source VS we have datas fresh enough stored
        write_file	=	True

	# We retrieve the configuration datas
        if data:

		# init output values
		if data.has_key('output'):
			data['data_output']	=	data['output']
			data.pop('output')

		if data.has_key('data_output')==False:
			dataoutput 		= 	{ 'type': 'json', 'encoding': 'utf-8' }
			data['data_output'] 	= 	dataoutput
		# default values (for dumps)
		default_output 			= 	{}

                default_output['type'] 		= 	"json"
                default_output['encoding'] 	= 	"utf-8"

                # We parse all the cache files having the source name
                parse           		=       "%s/tmp/%s_[0-9]*.json" % (cache_dir,source)
		try:
	                list            	=       glob.glob(parse)
		except Exception as e:
			message.addError('ETC_ERR_FILE_SYSTEM', 'Impossible to list file in sources directory (%s)' % parse, e)
		
                if len(list):
			# Current timestamp
			ts_curr 		= 	int(time.time())

			# We parse the dump files of the source
                        for i in range(len(list)):
				# We retrieve their timestamp
				ts_val 		= 	candles.getTimestampFile(list[i])
				# We check if there is a refresh time parametered VS we always process the queries
				if data.has_key('refresh'):
					try:
						ref	=	int(data['refresh'])
					except:
						ref	=	0
					# If the dump file is too old, we delete it
					if (ts_val + ref) < ts_curr:
						try:
							os.remove(list[i])
						except Exception as e:
							message.addError('ETC_ERR_FILE_OPERATION', "remove", list[i], e)
					# The dump file is recent enough, we can just retrieve the datas from it
					else:
						try:
							message.addMessage("ETC_STEP_MESSAGE", "Found a fresh data files for this source, system will return it")
							response = candles.getJsonToArray(file=list[i])
							write_file = False
						except Exception as e:
							message.addError('ETC_ERR_FILE_OPERATION', "read", list[i], e)
				# We always process the queries, no need to keep dump file
				else:
					try:
						os.remove(list[i])
					except Exception as e:
						message.addError('ETC_ERR_FILE_OPERATION',  "remove", list[i], e)

		# We prepare the source directory for output purposes
        	directory = "%s/dmp" % (cache_dir)
	        candles.make_sure_path_exists(directory)

		# We want to save the datas
		if write_file:
			try:
				# We lauch the process and retrieve a py dictionnary
				response	=	processMethod(data,source,is_lock,args)
			except:
				# We set an empty response
				response	=	False

		data_json	=	False
		if response:
			# the py dictionnary is converted in utf-8 json for dumps
		        data_json = dataOutput(response,default_output,source)

		# if it succeeded and we have a json output
		if data_json:
			if write_file:
				candles.writeInFile(data_json,("%s/tmp/%s_%s.json" % (cache_dir,source,ts))) 
			# if a treatment is already happing
			if is_lock:
				# We create a dump at the current timestamp
				filename = "%s/combine/%s_%s.json" % (cache_dir,source,ts)
				candles.writeInFile(data_json,filename)
			elif ( os.path.isfile( "%s/combine/%s_%s.json" % (cache_dir,source,ts) ) ):
				os.remove("%s/combine/%s_%s.json" % (cache_dir,source,ts) ) 

			# We create a dump having the sourcename in the source folder for an easy retrieve
			filename = "%s/dmp/%s.json" % (cache_dir,source)
        	        candles.writeInFile(data_json,filename)
		
		if os.path.isfile(curr_lock):
	        	# We remove the lock file
		        os.remove(curr_lock)
        	
		if response:
			try:
				# the real output as asked. Could return straight json or file/directory if xml,csv,sql
				return dataOutput(response,data['data_output'],source)
			except:
				return False
		else:
			return False
	else:
		if os.path.isfile(curr_lock):
	                # We remove the lock file
        	        os.remove(curr_lock)

		return False
	
# Merge data sources
def merge_data_sources( merge, result ):
	common_fields = []
	res_to_merge = { } 
	for s_name in merge:
		for source_name in result.keys():
			for s_name2 in result[source_name].keys():
				if ( s_name == s_name2):
					res_to_merge[s_name] = result[source_name][s_name]['data']
					if ( len(common_fields) == 0 ):
						common_fields = result[source_name][s_name]['data'][0].keys()
					else:
						record = result[source_name][s_name]['data'][0] 
						common_fields_tmp = []
						for common_f in common_fields:
							if record.has_key(common_f):
								common_fields_tmp.append(common_f)
						common_fields = common_fields_tmp
	resultat = []
	for s_name, records in res_to_merge.iteritems():
		for record in records:
			fields = record.keys()
			fields_to_delete = list_difference(fields, common_fields)
			for field in fields_to_delete:
				record.pop(field, None)
				to_add = True
				for record2 in resultat:
					fields_diff = set( record.keys() ) - set( record2.keys() )
					values_diff = set( record.values() ) - set( record2.values() ) 
					if ( len(fields_diff) == 0 and  len(values_diff) == 0 ):
						to_add = False
						break
				if to_add:
					resultat.append(record)

	# We use our data struture
	ret = { 'total': len(resultat), 'success': True, 'data': resultat}
	title = '_'.join( res_to_merge.keys() )
	ret = { title : ret }
	return { 'merge' : ret }
		
# Return an aray_diff
def list_difference(list1, list2):
	"""
	uses list1 as the reference, returns list of items not in list2
	"""
	diff_list = []
	for item in list1:
        	if not item in list2:
	            diff_list.append(item)
	return diff_list
		
# Opens the configuration file and lauch treatments
def processMethod(data,s_name, is_lock=False,args=False):
	"""
	retrieve attempted datas defined in the source configuration
	"""
	type_list 	= 	candles.getAllExtDataType()		
	results 	= 	{}

	message.debug	=	False
	if args and '-d' in args:
		message.debug = True

	# We retrieve the proxy configuration
	if data and data.has_key('proxy'):
		proxy 	= 	data['proxy']
	else:
		proxy 	=	False

	# 1. Observe the type of source (Database, File, ...)
	if data and data['data_sources']:
		# We want to process each source defined in the configuration
		for source in data['data_sources']:
	
			message.addMessage("ETC_STEP_MESSAGE", "Get data from source %s" % s_name )

			#If the source is well enough parametered
			if source['type'] != None and source['type'].lower() in type_list:
				try:
					# We init the class dynamically called using source-type
					module 		=	__import__( "app" )
					item		=	getattr(module, source['type'])()

					# We lauch our own init fct with our params
					item.init_generic( source, message, args, proxy ) 
					
					# We retrieve the results of all queries
					results[item.getName()] = item.getResult()

				except Exception as e:
					message.addError('ETC_ERR_LIBRARY', "lib : %s class: %s " % ( "app", source['type']) ,  e) 
			else:
				message.addError('ETC_ERR_CONFIG', "impossible to find an existing source type (%s). verify the value of type in %s/exec_src/%s.cfg" % (source['type'], resource_dir, source['type']), 2 )

		# If we want to merge the datas retrieved		
		if data.has_key('merge'):
			result 		= 	merge_data_sources(data['merge'], results)

		# if the source is locked we wait 3 seconds and we rechecked the lock value
		if ( is_lock ):
			# We parse all the cache files having the source name
		        parse           =       "%s/%s_*.lock" % (run_dir,source)
			try:
	        		list            =       glob.glob(parse)
			except Exception as e:
				list		=	False
				message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to list lock file in %s" % parse, e)
			# We use the timestamp for the file naming system
		        ts              =       int(time.time())
			is_lock==False
			sleep(3)
			# If we have lock files
			if list and len(list):
				for lock in list:
					# We retrieve the timestamp of the lock file
					ts_lock 	= 	candles.getTimestampFile(lock)
					# We don't consider lock files older than an hour
					if (ts - 3600) > ts_lock :
		                		if os.path.isfile(lock):
		                	        	# We remove the lock file
                		        		os.remove(lock)
					# If we have a lock file younger than an hour we consider the source running
					else: 
						is_lock = 	True
		# If we have post-treatments defined
		if ((data.has_key('post_treatments') and data['post_treatments']) or (data.has_key('src_pt') and data['src_pt'])) and is_lock==False:
                	# We parse all the cache files having the source name
                	parse           =       "%s/combine/%s_*.json" % (cache_dir,s_name)
			list		=	False
			try:
                		list	=       glob.glob(parse)
			except Exception as e:
				message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to list json file in %s" % parse, e)
                		
			# We check if we have other source files
			if list and len(list) > 0:
				# We parse the list of other source files
				for i in range(0, len(list)):
					# We retrieve the timestamp of the source file
					ts_val 		= 	candles.getTimestampFile(list[i])
					# We check if the lock file associated with the source file exists
					# We retrieve the old datas
					tmp_response 	= 	candles.getJsonToArray(file=list[i])
					# We merge data and tmp_response
					results 	= 	candles.combine(results,tmp_response)
					# We remove the lock file
					os.remove(list[i])
				# If we have datas
				if results.has_key('data'):
					results['total'] 	= 	len(results['data'])
	
                        # We process all post-treatments
                        for src, post in data['src_pt'].iteritems():

                                # We check if there are params
                                if not isinstance( post, basestring) and len(post.keys()):
                                        mypost                  =       post.keys()[0]
                                else:
                                        mypost                  =       post
                                if not isinstance( post, basestring) and len(post.values()):
                                        params                  =       post.values()[0]
                                else:
                                        params                  =       None

                                message.addMessage("ETC_STEP_MESSAGE", "Post Treatments %s for source %s called" % (mypost, src))

                                # First arg is file, second is function
                                tmp                             =       mypost.split('.')
                                function                        =       tmp[-1]
                                tmp.pop(-1)
                                if len(tmp) > 1:
                                        file                    =       tmp[-1]
                                        tmp.pop(-1)
                                        dir_to_add              =       "%s/lib/proc/%s" % (base,'/'.join(tmp))
                                        if dir_to_add not in sys.path:
                                                sys.path.append( dir_to_add)
                                else:
                                        file                    =       tmp[0]

                                # We try to process the treatment
                                try:
                                        module_post             =       __import__( file )
					if params.has_key('return') and params['return'] and params['return'].lower() == 'false':
						getattr(module_post, function )( results[src], data, params )
					else:
	                                        results[src]            =       getattr(module_post, function )( results[src], data, params, args )
                                except Exception as e:
                                        message.addError('ETC_ERR_LIBRARY', "module (%s) and class (%s)" % ( file, function ) , e )

			# We process all post-treatments
			for post in data['post_treatments']:

				# We check if there are params
				if not isinstance( post, basestring) and len(post.keys()):
					mypost 			= 	post.keys()[0]
				else:
					mypost                  =       post
				if not isinstance( post, basestring) and len(post.values()):
					params 			= 	post.values()[0]
				else:
					params 			= 	None
				message.addMessage("ETC_STEP_MESSAGE", "Post Treatments %s called" % mypost)


				# First arg is file, second is function
				tmp				=	mypost.split('.')
				function			=	tmp[-1]
				tmp.pop(-1)
				if len(tmp) > 1:
					file			=	tmp[-1]
					tmp.pop(-1)
					dir_to_add		=	"%s/lib/proc/%s" % (base,'/'.join(tmp))
					if dir_to_add not in sys.path:
						sys.path.append( dir_to_add)
				else:
					file			=	tmp[0]

				# We try to process the treatment
				try:	
					module_post 		=	__import__( file )
					results			=	getattr(module_post, function )( results, data, params, args )
				except Exception as e:
					message.addError('ETC_ERR_LIBRARY', "module (%s) and class (%s)" % ( file, function ) , e )
		return results
	else:
		return False

# Returns all the methods available
def allMethods(search=False):
	"""
		Send all the available methods
		aka. all the methods in the resources/configuration folder
	"""
	message.addMessage('ETC_STEP_MESSAGE', 'Request for getting all the sources available')
	# We init our vars
	sources 	= 	[ ]

	# We parse all the source files
	try:
		list	=	[]
                method_dir      =       "%s/exec_src" % resource_dir
                for root, dirs, files in os.walk(method_dir):
                        for file in files:
                                if file.endswith('.cfg'):
                                        url     =       '.'.join(os.path.join(root, file)[len(method_dir)+1:-4].split('/'))
                                        list.append(url)
	except Exception as e:
		message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to list data sources in %s" % parse, e )

	if list and len(list) > 0:
		for i in range(len(list)):
		
	        	# We get the configuration files datas
			data	=	candles.getConfigurationToArray(file=list[i])

        		# We make sure it went well
        		if  data:
                		# The name of the file aka the source
				filename	=	list[i]
				# Default values
				if data.has_key('name'):
					name = data['name']
				else:
					name = 'N/A'
				if data.has_key('description'):
					desc = data['description']
				else:
					desc = 'N/A'


                                if not search or search in name or search in filename:

                                        # We create a pre-formatted array to catch the datas
                                        sources.append(dict(
                                                        id                      =       i,                      # for canopsis
                                                        source                  =       filename,               # the filename
                                                        source_name             =       name,                   # to show in canopsis
                                                        source_description      =       desc                    # to show in canopsis
                                                ))
                                        print '**********************************************'
                                        print name
                                        print '----------------------------------------------'
                                        print 'SRC : ', filename
                                        print 'DSC : ', desc

                                        if 'data_sources' in data.keys() and len(data['data_sources']):
                                                arr     =       []
                                                for ds in data['data_sources']:
                                                        arr.append(ds['name'])
                                                print 'DS  :  %s' % ('\n       '.join(arr))
                                        if 'src_pt' in data.keys() and len(data['src_pt']):
                                                arr     =       []
                                                for src, tmp in data['src_pt'].iteritems():
                                                        arr.append("%s > %s" % (src, tmp.keys()[0]))
                                                print 'SCB :  %s' % ('\n       '.join(arr))
                                        if 'post_treatments' in data.keys() and len(data['post_treatments']):
                                                arr     =       []
                                                for cb in data['post_treatments']:
                                                        arr.append(cb.keys()[0])
                                                print 'CB  :  %s' % ('\n       '.join(arr))
                                        print


		# The datas in a Python Array
		data_file 	= 	dict(total=len(list), success=True, data=sources)
	else:
		data_file 	= 	dict(total=0, success=False)
	# We return the structured JSON
	return json.dumps( data_file, indent=4 )

def getAllMotorsToStart(cfg):
	sources		=	[]
	conf		=	candles.getConfigurationMultiToArray(cfg)
	arr_ignore	=	['general']
	required_dir	=	['dir','glob','param']
	if len(conf):
		for elt in conf:
			for src, arg in elt.iteritems():
				if 'dir.' == src[:4]:
					newsrc		=	src[4:]
					if set(required_dir).issubset(arg.keys()):
			                        # We parse all the cache files having the source name
			                        parse           =       "%s/%s" % (arg['dir'],arg['glob'])
                        			try:
			                                list            =       glob.glob(parse)
                        			except Exception as e:
			                                list            =       False
                        			        message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to find file in %s" % parse, e)
						if list:
							arg_list        =       []
							for key, value in arg.iteritems():
		                                                if key  == 'debug' and value.lower() == 'true':
                		                                        arg_list.append('-d')
                                		                elif key == 'force' and value.lower() == 'true':
                                                		        arg_list.append('-f')
		                                                elif key not in ['debug','force','return','dir','glob','param']:
                		                                        arg_list.append("%s=%s" % (key,value))
							for item in list:
								tmp_arg	=	arg_list[:]
								tmp_arg.append('%s="%s"' % (arg['param'],item))
								sources.append( {newsrc :  { 'return' : False, 'args' : tmp_arg } } )
					else:
						message.addMessage("Missing required parameters in Multi Configuration for source : %s" % (src))
				else:
					arg_list	=	[]
					ret		=	False
					for key, value in arg.iteritems():
						if key	== 'debug' and value.lower() == 'true':
							arg_list.append('-d')
						elif key == 'force' and value.lower() == 'true':
							arg_list.append('-f')
						elif key == 'return' and value.lower() == 'true':
							ret	=	True
						elif key not in ['debug','force','return']:
							arg_list.append("%s=%s" % (key,value))
					sources.append( {src :	{ 'return' : ret, 'args' : arg_list } } )
	return sources

# Returns all the methods available
def allMethodsMulti():
        """
                Send all the available methods
                aka. all the methods in the resources/configuration folder
        """
        message.addMessage('ETC_STEP_MESSAGE', 'Request for getting all the multi sources available')
        # We init our vars
        sources         =       [ ]

        # We parse all the source files
        try:
                list    =       []
                method_dir      =       "%s/multi" % resource_dir
                for root, dirs, files in os.walk(method_dir):
                        for file in files:
                                if file.endswith('.cfg'):
                                        url     =       '.'.join(os.path.join(root, file)[len(method_dir)+1:-4].split('/'))
                                        list.append(url)
        except Exception as e:
                message.addError('ETC_ERR_FILE_SYSTEM', "Impossible to list data sources in %s" % parse, e )

        if list and len(list) > 0:
                for i in range(len(list)):
                        # We get the configuration files datas
                        res    =       candles.getConfigurationMultiToArray(file=list[i])
                        # We make sure it went well
                        if res:
				for data in res:
					for key, val in data.iteritems():
						if key == "general":
			                                # The name of the file aka the source
        			                        filename        =       list[i]
		                	                # Default values
                		        	        if val.has_key('name'):
                                			        name = val['name']
			                                else:
        			                                name = 'N/A'
                	        		        if val.has_key('description'):
                        	                		desc = val['description']
		                                	else:
	        		                                desc = 'N/A'

							list_src        =       getAllMotorsToStart(filename)
							exe		=	[]
							for x in list_src:
								for y,z in x.iteritems():
									if y != 'general':
										exe.append("%s %s" % (y,' '.join(z['args'])))
        	                		        
							# We create a pre-formatted array to catch the datas
		                	                sources.append(dict(
                		                                id                      =       i,                      # for canopsis
		                                                source                  =       filename,               # the filename
                		                                source_name             =       name,                   # to show in canopsis
                                		                source_description      =       desc                    # to show in canopsis
		                                        ))
		                        	        print '**********************************************'
	        		                        print name
        	                		        print '----------------------------------------------'
		                	                print 'SRC : ', filename
                		        	        print 'DSC : ', desc
							print 'EXE : ', ', '.join(exe)
                                			print


                # The datas in a Python Array
                data_file       =       dict(total=len(list), success=True, data=sources)
        else:
                data_file       =       dict(total=0, success=False)
        # We return the structured JSON
        return json.dumps( data_file, indent=4 )


# End key.py
