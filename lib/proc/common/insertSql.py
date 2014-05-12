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


from camqp import camqp
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
def record_exists(db, record, table, pk):
	select = "select * from %s where %s=\"%s\"" %(table, pk, record[pk] ) 
	res = db.select( select )
	if len(res) > 0 :
		return True
	else:
		return False

def do_update(db, record, table, pk):
	query = "update %s set %s where %s=\"%s\"" % (table, ",".join(["%s=\"%s\"" % (k, v) for k, v in record.items()]) , pk, record[pk] ) 
	r = db.conn.cmd_query(query)
	db.cmd('COMMIT')

def do_insert(db, record, table, pk):
	query = "insert into %s (%s) VALUES (%s)" % (table, ",".join( record.keys() ), ",".join(["\"%s\"" % (v) for k, v in record.items()]) )
	r = db.conn.cmd_query(query)
	db.cmd('COMMIT')

def insertSql( resultats, settings, params, args ):
	if params.has_key('Database'):
		dbconfile = "%s/Database/%s.json" % ( resource_dir, params['Database'] ) 
		dbconf  = getJsonToArray(dbconfile)
		db = 	bibsql.sqldb(conf=dbconf)
	else :
		return
	if params.has_key('primary'):
		pk = params['primary']
	else:
		return
	if params.has_key('table'):
		table = params['table']
	else:
		return
	
	for source,query in resultats.items():
		for q_name,records in query.items():
			for record in records['data']:
				if record.has_key(pk): 
					if record_exists( db, record, table, pk) :
						do_update(db, record, table, pk)
					else:
						do_insert(db, record, table, pk)

	return resultats

	
