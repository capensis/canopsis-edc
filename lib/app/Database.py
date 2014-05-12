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


# We implement the JSON libraries
import sys
import os

global base
base = os.environ['EDC_HOME']
global resource_dir
resource_dir	=	base+"/cfg/";
global log_dir
log_dir = os.environ['EDC_LOG']

#import settings
from connector import biblog, bibutils, bibsql
#bibtools

import simplejson as json

from edc_lib import candles
from connector.bibsql import BibSql
from Base import Base


# Lib for Messages
from app.Message import Message
global message
message = Message( log_dir )

class Database (Base):

	def __init__(self):
		pass

        # init function
        def init(self):
		try:
			# the database configuration file
			tmp			=	self.conf['instance'].split('.')
			source     		=       "%s/db/%s.json" % (resource_dir,tmp[0])
			self.name		=	self.conf['name']
			self.encode_orig	=	False
		except Exception as e:
			source			=	""
			message.addError('ETC_ERR_FILE_OPERATION', 'read', file, e)

		# We affect the configuration infos
		try:
			self.settings		=	candles.getConfigDatabase(file=self.conf['instance'])
			self.settings['SID']	=	self.settings['sid']
		except  Exception as e :
                        self.message.addError("ETC_ERR_STEP","Impossible to retrieve the connection information for '%s'" % self.conf['instance'],  e)

		# We connect to the db via bibsql
		try:
			self.db = 	bibsql.sqldb(conf=self.settings)
		except Exception as e :
			self.message.addError("ETC_ERR_DATABASE","Connection failed",  e)
		
		self.getData_generic()

        # returns the datas from the source
        def getData(self):
		results = { }
		#for query in self.conf['list_queries']:
		if self.conf['query'] and self.conf['query']!='False':

			query	=	self.conf

                        if self.args:
                                for arg in self.args:
                                        if arg[:(len(self.name)+1)] == (('%s.') % self.name) and arg.find('=') != -1 :
                                                params_string   =       arg[(len(self.name)+1):]
                                                position_val    =       params_string.find('=')
                                                param_name      =       params_string[:position_val]
                                                param_val       =       params_string[position_val+1:]

                                                if query['query'] and query['query'].find('{%s}' % param_name) != -1:
                                                        query['query']  =       param_val.join(query['query'].split('{%s}' % param_name))

                        if query.has_key("encode_origin"):
                                self.encode_orig = query["encode_origin"]
                        else:
                                try:
                                        query['query']  =       query['query'].encode('raw_unicode_escape')
                                except:
                                        pass

                        try:
                                self.query_name = query['name']
                        except Exception as e:
                                self.message.addError("ETC_ERR_STEP","Imposible to find a query name : %s" % e)

			if query.has_key('limit') and query['limit']!= 'False':
                        	limit   =       int( query['limit'] )
                        else:
                        	limit   =       False

                        if ( query['query'] ) :
                                query_msg       =       query['query']
				self.res	=	[]
                                try:
                                        query_msg       =       candles.remove_accents(candles.try_unicode(query_msg))
                                except:
                                        pass

                                self.current_query = query

                                if ( query.has_key('mapping') ):
                                        self.current_mapping = query['mapping']
                                else:
                                        self.current_mapping = None

                                try:
					if limit and limit > 0:
                                                self.res = self.db.select(query['query'],limit)
                                        else:
                                                self.res = self.db.select(query['query'])

                                except Exception as d:
                                        try:

                                                s1      =       query['query']
                                                s2      =       query['query']
                                                try:
                                                        s2 = unicode(eval('"'+s1+'"'), self.encode_orig)
                                                except:
                                                        try:
                                                                s2 = unicode(eval('"'+s1+'"'), 'utf8')
                                                        except:
                                                                try:
                                                                        s2 = unicode(eval('"'+s1+'"'), 'iso-8859-1')
                                                                except:
                                                                        pass

                                                        query['query']  =       s2
                                                        if limit and limit > 0:
                                                                self.res = self.db.select(query['query'],limit)
                                                        else:
                                                                self.res = self.db.select(query['query'])

                                        except Exception as e:

                                                try:
                                                        query['query']  =       query['query'].encode('raw_unicode_escape')
                                                except:
                                                        pass

                                                try:

                                                        s1      =       query['query']
                                                        s2      =       query['query']
                                                        try:
                                                                s2 = unicode(eval('"'+s1+'"'), self.encode_orig)
                                                        except:
                                                                try:
                                                                        s2 = unicode(eval('"'+s1+'"'), 'utf8')
                                                                except:
                                                                        try:
                                                                                s2 = unicode(eval('"'+s1+'"'), 'iso-8859-1')
                                                                        except:
                                                                                pass

                                                        query['query']  =       s2
							if limit and limit > 0:
                                                                self.res = self.db.select(query['query'],limit)
                                                        else:
                                                                self.res = self.db.select(query['query'])

			                                self.message.addMessage( "ETC_STEP_MESSAGE", "Query : %s executed" % query_msg )


                                                except Exception as e:
                                                        self.message.addError("ETC_ERR_DATABASE", 2, "Impossible to execute query (%s)" % (query_msg),  e)
				self.treatData_generic()
				self.formatData_generic()
				results = self.result
				self.result = {} 
				self.current_mapping = {}
				self.current_query = {}
			else :
				self.message.addError('ETC_ERR_CONFIG', 'Impossible to find query')
		if ( self.settings and self.settings.has_key('db_type') and self.settings['dbtype'] == 'MSSQL' ):
			self.db.restaure_prev_environ_var
		self.data = results

        # catches the datas and launch the request
        def treatData(self):
		self.message.addMessage("ETC_STEP_MESSAGE", "Treating data")
		data_tmp = []
		desc_tmp = []
		
		# decode datas
		if self.encode_orig:
			self.res = candles.dataDecodeEncode(self.res,self.encode_orig,'ascii')
		
		# gets each row
		try:
			if len(self.res):
		                for row in self.res:
					data_tmp.append(row)
			else:
				self.message.addError('ETC_STEP_MESSAGE', 'No data to treat')
		except Exception as e:
			self.message.addError('ETC_STEP_MESSAGE', 'No data to treat')

		self.result['data'] = data_tmp
		self.result['success'] = 'true'
		self.result['total'] = len(data_tmp)
	
		# Returns the fields information - description=True in configuration
		try:
			if self.current_query.has_key('description') and self.current_query['description'] and self.current_query['description']!='False' :
        			for desc in self.db.description:
					row_desc_tmp = {}
					row_desc_tmp['name'] = getattr(desc,'name')
					if self.settings["dbtype"] == 'ORACLE':
						row_desc_tmp['type'] = repr( getattr(desc,'type'))
					else:
						row_desc_tmp['type'] = getattr(desc,'type')
					row_desc_tmp['display_size'] = getattr(desc,'display_size')
					row_desc_tmp['internal_size'] = getattr(desc,'internal_size')
					row_desc_tmp['precision'] = getattr(desc,'precision')
					row_desc_tmp['scale'] = getattr(desc,'scale')
					row_desc_tmp['null_ok'] = getattr(desc,'null_ok')
	
        	        		desc_tmp.append(row_desc_tmp)
	
				self.result['description'] = desc_tmp
		except Exception as e:
			self.message.addError("ETC_ERR_STEP", "Error during treating data : %s" % e)

		self.formatData_generic()

	def formatData(self):
		self.message.addMessage("ETC_STEP_MESSAGE", "Formating Data")

#End Database.py
