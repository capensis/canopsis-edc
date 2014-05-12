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

import sys
import os
import simplejson as json
from app import dynamic_values
from edc_lib import candles
from datetime import date, datetime, timedelta

# The parent class for all types
class Base:

        # init function
        def __init__(self):
                pass
	
	# set vars
	def init_generic(self, conf, message, args, proxy):
		# we store the configuration file
		self.name	=	"no_name"
                self.conf	=	conf
		self.message	=	message
		self.args	=	args
		self.proxy	=	proxy
		self.data	=	[] #{ }
		self.result	= 	{ }
		self.query_name =	'no_name'
		self.current_mapping	=	{}
	
		self.init()

	# to override
	def init(self):
		self.getData_generic()

	# before getData
	def getData_generic(self):
		self.getData()

        # returns the datas from the source
        def getData(self):
                self.treatData_generic()

	# converts python datas into json
	def convert_to_json(self):
		pass

        # returns the datas from the source
        def getDataFile(self):
                results = { } 
                if self.conf:
			file		=	self.conf
                        self.file	=	file
			if self.file.has_key("encode_origin"):
				self.encode_orig = self.file["encode_origin"]
			else:
				self.encode_orig = 'utf-8'
			try:
				self.query_name = file['name']
			except Exception as e:
				self.message.addError('ETC_ERR_CONFIG',  "No name found for the file query : %s " % e )
			if ( file.has_key('mapping') ):
				self.current_mapping = file['mapping']
			else:
				self.current_mapping = {}
                        if (file.has_key("dynamic") and file["dynamic"]) or (file.has_key("url") and file["url"]) :
				if file.has_key("dynamic") and file["dynamic"] and file["dynamic"].lower()!='false':
                                        if len(self.args) and file.has_key("param_name"):
                                                for arg in self.args:
                                                        tmp_arg = arg.split("=")
							if len(tmp_arg) == 1:
								tmp_arg = arg.split(":")
                                                        if tmp_arg[0] == file["param_name"]:
                                                                try:
                                                                	self.filename = tmp_arg[1]
									self.content = candles.getFileContent(self.filename,self.encode_orig,self.proxy)
                                                                	self.result['data'] = self.convert_to_json()
                                                                except Exception as e:
                                                                        self.message.addError('ETC_ERR_FILE_OPERATION', 'read', self.filename, e)
                                                                break
                                	else:
                                        	self.message.addError('ETC_ERR_CONFIG', 'Impossible to match the call with the configuration')
				else:
                                	try:
                                        	self.filename = file['url']
		                        	self.content = candles.getFileContent(self.filename,self.encode_orig,self.proxy)
        		                        self.result['data'] = self.convert_to_json()
                                        except Exception as e:
                                                self.message.addError('ETC_ERR_FILE_OPERATION', 'read',self.filename, e)

				self.content = ""
                                self.treatData_generic()
				results = self.result
                                self.result = {}
                                self.current_file = {}
                        else :
                                self.message.addError('ETC_ERR_CONFIG', 'Impossible to find file in configuration')
			self.current_mapping = { }
                self.data = results
	
	# before treatData
	def treatData_generic(self):
		self.treatData()
        
	# catches the datas and launch the request
        def treatData(self):
                if self.result.has_key('data') == False:
                        self.result['data'] = []
                self.result['success'] = 'true'
		if self.result['data']:
	                self.result['total'] = len(self.result['data'])
		else:
			self.result['total'] = 0

		self.formatData_generic()

	# treats dynamic values
	def formatData_generic(self):
		tmpdata = []
		if self.result.has_key('data') and self.result['data']:
			if type(self.result['data']) == dict:
				self.result['data'] = self.result['data'].values()
			for result in self.result['data']:
				fields = result.keys()
				newresult = { }
				if (self.current_mapping and  self.current_mapping.has_key( 'fields_renaming' ) ):
					try:
						for fnamemapped, values in self.current_mapping['fields_renaming'].items():
							fnameorig 	=	values[0]
							copie		=	values[1]
							retour		=	values[2]
							if ( len(values) == 4 ):
								force_type = values[3]
							else:
								force_type = False
							if not fnameorig in fields:
								self.message.addError('ETC_ERR_CONFIG', 'The field %s does not exist in the result of query' % ( fnameorig ))
							else:
								if type (result[fnameorig]) is date or type(result[fnameorig]) is datetime:
									result[fnameorig] = result[fnameorig].strftime('%Y-%m-%d %H:%M:%S')
								if ( force_type ):
									if (force_type == 'int'):
										newresult[fnamemapped] = int(result[fnameorig])
									else:
										newresult[fnamemapped] = result[fnameorig]
								else:
									newresult[fnamemapped] = result[fnameorig]
								if copie:
									newresult[fnameorig] = result[fnameorig]
									
					except Exception as e:
						self.message.addError("ETC_ERR_CONFIG", "Error during mapping > renaming fields : %s" % e)
				
				for field in fields:
					try:
						if type(result[field]) is date or type(result[field]) is datetime :
							result[field] = result[field].strftime('%Y-%m-%d %H:%M:%S')
						elif type(result[field]) is timedelta:
							result[field] = result[field].total_seconds()
					except Exception as e:
						pass
						#self.message.addError("ETC_ERR_CONFIG", "Error during converting datetime field in string field for json export : %s" % e)
					try:
						if ( self.current_mapping and self.current_mapping.has_key('prefix') ):
							newresult[self.current_mapping['prefix']+field] = result[field]
						else:
							newresult[field] = result[field]
					except Exception as e:
						self.message.addError("ETC_ERR_CONFIG", "Error during prefixing field : %s" % e)

				try:
					if ( self.current_mapping and self.current_mapping.has_key('records_constants') ):
						for fname, value in self.current_mapping['records_constants'].items() :
							newresult[fname] = value
				except Exception as e:
					self.message.addError("ETC_ERR_CONFIG", "Error during adding constants records : %s" % e )
	
				try:
					if ( self.current_mapping and self.current_mapping.has_key('dynamic_values') ):
						for fname, value in self.current_mapping['dynamic_values'].items() :
							if value.has_key('function') and value['function'].has_key('name'):
								try:
									function_name		=	value['function']['name']
				        	                        newvalue                =       getattr( dynamic_values, function_name )
									newresult[fname]	=	newvalue( value, result)
								except Exception as e:
									self.message.addError("ETC_ERR_LIBRARY", function_name, e)
				except Exception as e:
					self.message.addError("ETC_ERR_CONFIG", "Error during calculating dynamic values : %s" % e)
				try:
					if ( self.current_mapping and self.current_mapping.has_key("delete_fields") ):
						for f_delete in self.current_mapping['delete_fields']:
							if ( newresult.has_key(f_delete) ):
								newresult.pop( f_delete, None)
				except Exception as e:
					self.messsage.addError("ETC_ERR_FILE_OPERATION", "Error during deleting files : %s" % e )

				tmpdata.append(newresult)
		if ( len(tmpdata) > 0 ):
			self.result['data'] = tmpdata 
		self.result['mapping'] = self.current_mapping	
		self.formatData()

        # formats the datas according the requested format
        def formatData(self):
		pass

	# returns data
	def getResult(self):
		return self.data

	# returns name
	def getName(self):
		return self.name

# End Base.py
