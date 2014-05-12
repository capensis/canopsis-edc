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


from copy import deepcopy
import json, os
global base
base = os.environ['EDC_HOME']

import sys
#We import the right library path
from edc_lib import candles
from datetime import datetime
import time

from connector import bibsql
import unicodedata

def remove_accents(input_str):
        nkfd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nkfd_form.encode('ASCII', 'ignore')
        return only_ascii


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

def do_query(query, db):
	try:
	        r = db.conn.cmd_query(query)
	except:
		query	=	remove_accents(try_unicode(query))
		r = db.conn.cmd_query(query)
	db.cmd('COMMIT')

def createTable(data, conf, params, args):
	new_params	=	{}
	if params:
		for key, val in params.iteritems():
			tmp	=	key.split('.')
			if len(tmp) == 2:
				p                       =       {}
                                p[tmp[1]]               =       val
				if tmp[0] not in new_params.keys():
					new_params[tmp[0]]	=	p
				else:
					new_params[tmp[0]].update(p)
			elif len(tmp) == 3:
				if tmp[1] == "fields_additional":
                                	p                       =       {}
                                        p[tmp[2]]               =       val.split(',')

                                        if tmp[0] not in new_params.keys():
                                                new_params[tmp[0]]      =       {}

					if new_params[tmp[0]].has_key('fields_additional') == False:
						p0      =       { 'fields_additional' : p }
						new_params[tmp[0]].update(p0)
					else:
						temp	=	new_params[tmp[0]]
						temp['fields_additional'].update(p)
						new_params[tmp[0]]	=	temp
	if data:
        	for source in data.keys() :
			if source.lower() in new_params.keys():
				parameters	=	new_params[source.lower()]
			        if parameters.has_key('database'):
       	        			dbconf  	=	candles.getConfigDatabase(parameters['database'])
	        			db 		=	bibsql.sqldb(conf=dbconf)
	        		else :
					message.addError("ETC_ERR_CONFIG", "Missing 'database' parameter for %s" % source )
       		        		return
       		
                                if parameters.has_key('tablename'):
					table   =       parameters['tablename']
				else :
                                        message.addError("ETC_ERR_CONFIG", "Missing 'tablename' parameter for %s" % source )
					return
			
                                row 	= 	data[source]

       	                        if row.has_key('data') and row['data'] and db:
					if parameters.has_key('drop') and parameters['drop']:
	 	                        	query_drop   	=       "DROP TABLE IF EXISTS %s;" % (table)
       	                                        do_query(query_drop, db)

					q		=	[]
					add_f		=	[]
					add_v		=	[]
					not_constant	=	["timestamp","date"]
					if parameters.has_key("fields_additional") and parameters['fields_additional']:
						for key,val in parameters['fields_additional'].items():
	                                                primary         =       ""
                                                        if parameters.has_key("primary") and parameters['primary'] and key == parameters['primary']:
        	                                                primary =       "PRIMARY KEY"
							q.append( ( "%s %s %s" % (key,val[0],primary) ) )

							add_f.append(key)
	
							if val[1] not in not_constant:
								add_v.append(val[1])

					for record in row['data']:
						for key in record.keys():
							primary		=	""
							if parameters.has_key("primary") and parameters['primary'] and key == parameters['primary']:
								primary	=	"PRIMARY KEY"
							if parameters.has_key("fields_info") and parameters['fields_info']:
								if parameters['fields_info'].has_key(key) and parameters['fields_info'][key]:
									q.append( ( "%s %s %s" % (key,parameters['fields_info'][key],primary) ) )
								else:
									q.append( ( "%s %s %s" % (key,"VARCHAR(255) DEFAULT ''",primary) ) )
							else:
								q.append( ( "%s %s %s" % (key,"VARCHAR(255) DEFAULT ''",primary) ) )
						break

					query_create    =       "CREATE TABLE IF NOT EXISTS %s (%s);" % ( table, ', '.join(q) )

                                        do_query(query_create, db)
	                                for record in row['data']:
						comma	=	""
						vals	=	list(set(record.values()))
						if len(add_f):
	        	                               	comma    =       ","
						if len(vals)>1 and set(vals).issubset(['',' ',False]) == False:
							query_insert    =       "INSERT INTO %s (%s %s %s) VALUES (%s,%s)" % (table, ",".join(add_f), comma, ",".join( record.keys() ), ",".join(add_v), ",".join(["\"%s\"" % (v) for k, v in record.items()]) )
							do_query(query_insert, db)

        return data
	
