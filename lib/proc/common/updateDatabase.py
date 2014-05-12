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
base = os.environ['HOME_CONNECTEUR']
if not os.environ.has_key('HOME_CONNECTEUR') or os.environ['HOME_CONNECTEUR'] == '':
	dir_path = os.path.dirname(os.path.abspath(__file__))
	home_connecteur = "%s/../../" % dir_path
	os.environ['HOME_CONNECTEUR'] = home_connecteur

base = os.environ['HOME_CONNECTEUR']
global cache_dir
if (os.environ.has_key( 'HOME_CONNECTEUR_CACHE_DIR' ) ):
	cache_dir = os.environ['HOME_CONNECTEUR_CACHE_DIR'] 
else:
	cache_dir = ("%s/cache" % (base) ) 

global resource_dir
if ( os.environ.has_key('HOME_CONNECTEUR_RESOURCE_DIR') ):
	resource_dir = os.environ['HOME_CONNECTEUR_RESOURCE_DIR']
else:
	resource_dir = ("%s/resources" % (base) )
global log_dir
if ( os.environ.has_key('HOME_CONNECTEUR_LOG_DIR' ) ) :
	log_dir = os.environ['HOME_CONNECTEUR_LOG_DIR'] 
else:
	log_dir = ( "%s/log" % (base ) )

import sys
#We import the right library path
sys.path.append( "%s" % ( base ) )
sys.path.append( os.environ['HOME_CONNECTEUR']+"/lib/python")
sys.path.append( os.environ['HOME_CONNECTEUR']+"/lib/python2.7")
from controller_library.candles import getJsonToArray
from datetime import datetime
import time

from connector import bibsql

#from connector.biblog import BibLog

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
		print query
	        #r = db.conn.cmd_query(query)
	except:
		query	=	remove_accents(try_unicode(query))
		#r = db.conn.cmd_query(query)
		print query
	#db.cmd('COMMIT')


def mergeData(data, conf, params, args):
	if data:

		if params.has_key('key') and params.has_key('source_names') and params.has_key('table_ref') and params.has_key('tables_merge'):
			pass
		else:
			print "missing params"
                        return data

		check_ok	=	0
		array_conflict	=	{}
		array_merge     =       {}
		conflict	=	0
		for instance in data:
			for sources in params['source_names']:
				for source, filters in sources.items():

					array_merge[source]	=       {}
					array_conflict[source]  =       {}
					if source in data[instance].keys() and data[instance][source].has_key('data') and data[instance][source]['data'] and params['key'] in data[instance][source]['data'][0].keys():

						check_ok        +=      1

						for row in data[instance][source]['data']:

							add_to_result	=	True

                                                	if filters.has_key("filter") and filters["filter"]:

                                                                for field, match in filters["filter"].iteritems():
                                                                	if row.has_key(field) and row[field].lower() != match:
                                                                       		add_to_result   =       False
                                                                                break

							if filters.has_key("retrieve") and filters["retrieve"] and add_to_result:
                                                                tmp     =       {}
                                                                for key,val in row.items():
                                                                	if key in filters["retrieve"]:
                                                                		tmp[key]        =       val
							else:
								tmp	=	row

							if add_to_result:
								nmhost	=	row[params['key']]
								if nmhost not in array_merge[source].keys():
									array_merge[source][nmhost]	=	tmp
								else:
									conflict	+=	1
									array_conflict[source][nmhost]	=	[ tmp , array_merge[source][nmhost]  ]
									array_merge[source].pop(nmhost)

					print array_conflict[source]
	
		if array_merge.has_key( params['table_ref'] ) and array_merge[params['table_ref']]:

                        check_table = array_merge.keys()
			check_table.remove( params['table_ref'])

	                has_correct_data        =       set( params['tables_merge'] ).issubset( set ( check_table ) )

			if has_correct_data:
				to_delete	=	[]
				for nmhost, item in array_merge[params['table_ref']].iteritems():
					for table_merge in check_table:
						if array_merge[table_merge].has_key(nmhost) and array_merge[table_merge][nmhost]:
							array_merge[params['table_ref']][nmhost].update(array_merge[table_merge][nmhost])
						else:
							to_delete.append(nmhost)

				for nmhost in to_delete:
					array_merge[params['table_ref']].pop(nmhost)

				print "size deleted : ", len(to_delete)
				print "conflict : ", conflict
				print "size ok : ", len(array_merge[params['table_ref']])
	
        return array_merge[params['table_ref']]
	
