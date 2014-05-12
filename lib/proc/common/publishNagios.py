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
base = os.environ['EDC_HOME']
global log_dir
log_dir	= os.environ['EDC_LOG']
global var_dir
var_dir = os.environ['EDC_VAR']

import sys
#We import the right library path
from edc_lib import candles
from datetime import datetime
import time

from connector import bibsql

import pynsca

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

def publishInNagiosSource( resultats, settings, params, args ):
        #you can add host, port, userid, password, virtualhost, exchange_name, read_conf_file, auto_connect, on_ready
        if ( params.has_key('connect_host') ):
                host = params['connect_host']
        else:
                host = "localhost"
        if ( params.has_key('connect_port') ):
                port = int(float(params['connect_port']))
        else:
                port = 5667
        if ( params.has_key('connect_mode') ):
                mode = int(float(params['connect_mode']))
        else:
                mode = 1
		# 1 : standard
		# 3 : Crypto.Cypher
		# 16 : mcrypt
        if ( params.has_key('connect_password') ):
                password = params['connect_password']
        else:
                password = None

	notif 	=	pynsca.NSCANotifier(host,port,mode,password)

        record_fail = []
        num_del_record = 0
        newdata = None
        cmpt = 0
 	fail = 0

	if notif:
                # We now send the new publications
                newresultat = {}
		newdata = []
                #for source,query in resultats['data'].items():
		for record in resultats['data']:
			try:
				if set(['host_name','svc_description','return_code','plugin_output']).issubset(record.keys()) :
					host_name       =       record['host_name']
        	                        svc_description =       record['svc_description']
                	                return_code     =       int(float(record['return_code']))
                        	        # OK = 0
                                	# WARNING = 1
	                                # CRITICAL = 2
        	                        # UNKNOWN = 3
                	                plugin_output   =       record['plugin_output']
	                                inserted	=	notif.svc_result(host_name,svc_description, return_code, plugin_output)
				else:
					print "missing key in the result : host_name,svc_description,return_code,plugin_output mandatory"
			except Exception as e:
				print e
                                fail += 1
	else:
		fail	=	len(resultats['data'])
	print len(resultats['data']), " records with ", fail, " failed"
        return resultats

def publishInNagios( resultats, settings, params, args ):
	newdata	=	{}
	for src,data in resultats.iteritems():
		if data.has_key('data'):
			newdata[src]	=	publishInNagiosSource( data, settings, params, args )
	return newdata


def publishInNagiosDistrib( resultats, settings, params, args ):
        newdata =       {}
	for exe,vals in resultats.iteritems():
		if len(vals.keys()):
		        for src,data in vals.iteritems():
				new_params	=	params.copy()
				if src != 'default':
					new_params['connect_host']	=	src
	        	        if data and data.has_key('data'):
        	        	        newdata[src]    =       publishInNagiosSource( data, settings, new_params, args )
        return newdata

def updateTable ( resultats, settings, params, args ):
        instance = None
        if ( params.has_key('instance') ):
                instance = params['instance']
        table = None
        if ( params.has_key('table') ):
                table = params['table']
        fieldid = None
        if ( params.has_key('fieldid') ):
                fieldid = params['fieldid']
        idstk = None
        if ( params.has_key('id') ):
                idstk = params['id']
        keyid = None
        if ( params.has_key('keyid') ):
                keyid = params['keyid']
        keydt = None
        if ( params.has_key('keydt') ):
                keydt = params['keydt']



        settings        =       candles.getConfigDatabase(instance)
        db              =       bibsql.sqldb(conf=settings)

        for key,source in resultats.iteritems():
                if source.has_key('data') and source['data']:
                        for record in source['data']:
                                fieldidvalue = record[fieldid]
                                dtsync = datetime.now()
                                str1 = "UPDATE %s set %s=NOW() where %s=%s and %s=%s" % (table, keydt, fieldid, fieldidvalue, keyid, idstk )
                                r = db.update(str1)
                                db.commit()

        return resultats

