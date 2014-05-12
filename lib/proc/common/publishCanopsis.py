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


import sys, os
from camqp import camqp
from copy import deepcopy
import json

global base
base = os.environ['EDC_HOME']
global log_dir
log_dir	= os.environ['EDC_LOG']
global var_dir
var_dir = os.environ['EDC_VAR']

#We import the right library path
from edc_lib import candles
from datetime import datetime
import time

from connector import bibsql

def formatRoutingKey ( record ) :
	connector	=	"ExtDataSource"
	connector_name	=	"ExtDataSource_1"
	event_type	=	"check"
	source_type	=	"resource"
	component	=	record['component']
	resource	=	record['resource']
	
	return "%s.%s.%s.%s.%s.%s" % ( connector, connector_name, event_type, source_type, component, resource) 

def build_arbo ( array, value, recursion=0):
	resultat = {}
	if ( len(array) == 1):
		indice = array[0]
		resultat[indice] = value
		return resultat
	elif ( recursion < 3) :
		recursion = recursion + 1
		indice = array[-1]
		resultat[indice] = value
		return build_arbo( array[:-1], resultat, recursion )

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

def recordFailedBusPublication(records):
	if len(records):
		canop_file           =       "%s/cache/tmp/canopsis.json" % (var_dir)
		tmp_content = candles.getJsonToArray(canop_file)
	        if tmp_content == False:
        	        tmp_content = []

		for curr_record in records:
			curr_key =  curr_record.keys()[0]
			tmp_content.append(curr_record)

		f = open(canop_file,"w+")

		json.dump(tmp_content,f)

def recordProcessedBusPublication(records):
	if len(records):		
                canop_file           =       "%s/cache/tmp/canopsis.json" % (var_dir)
                f = open(canop_file,"w+")
                json.dump(records,f)


def publishInCanopsisSource( resultats, settings, params, args ):
        #you can add host, port, userid, password, virtualhost, exchange_name, read_conf_file, auto_connect, on_ready
        if ( params.has_key('amqp_host') ):
                amqp_host = params['amqp_host']
        else:
                amqp_host = "localhost"
        if ( params.has_key('amqp_port') ):
                amqp_port = params['amqp_port']
        else:
                amqp_port = 5672
        if ( params.has_key('amqp_userid') ):
                amqp_userid = params['amqp_userid']
        else:
                amqp_userid = "guest"
        if ( params.has_key('amqp_password') ):
                amqp_password = params['amqp_password']
        else:
                amqp_password = "guest"
        if ( params.has_key('amqp_virtualhost') ) :
                amqp_virtualhost = params['amqp_virtualhost']
        else:
                amqp_virtualhost = "canopsis"
        if ( params.has_key('amqp_exchange') ):
                amqp_exchange = params['amqp_exchange']
        else:
                amqp_exchange = "canopsis.events"
	try:
	        amqp_bus = camqp(host=amqp_host, port=amqp_port, userid=amqp_userid, password=amqp_password, virtual_host=amqp_virtualhost, exchange_name="canopsis.events" )
	except Exception as e:
		print e
        record_fail = []
        num_del_record = 0
        newdata = None
        cmpt = 0 
	if amqp_bus:
                # We treat the waiting publications
                canop_content = False
                try:
                        canop_file           =       "%s/cache/tmp/canopsis.json" % (var_dir)
                        if ( os.path.isfile( canop_file ) ) :
                                canop_content        =       getJsonToArray(canop_file)
                except Exception as e:
                        pass
                if canop_content:
                        i               =       0
                        canop_to_pop    =       []
                        while i < len(canop_content):
                                record = canop_content[i]
                                curr_key = record.keys()[0]
                                inserted =amqp_bus.publish(json.dumps(record[curr_key]),curr_key)
                                if ( inserted ):
                                        canop_to_pop.append(i)
                                        num_del_record += 1
                                else:
                                        pass
                                i = i+1
                        for item in canop_to_op:
                                canop_content.pop(item)
                if num_del_record > 0:
                        recordProcessedBusPublication(canop_content)

                # We now send the new publications
                newresultat = {}
		newdata = []
                #for source,query in resultats['data'].items():
		for record in resultats['data']:

                        newrecord = {}
                        tmplevel = {}
                        remove = []
                        for field, value in record.items():

                        	if 'metric.' in field and record.has_key( field.split('.')[1] ) and record[field.split('.')[1]] and field.split('.')[2] and field.split('.')[0]:
                                        record[ field.split('.')[0]+"."+record[field.split('.')[1]]+"."+field.split('.')[2] ] = value
                                        remove.append(field)

                                if record.has_key('timestamp') and ( type( record["timestamp"] ) is not int ):
                                        dtime = datetime.strptime( record['timestamp'], '%Y-%m-%d %H:%M:%S')
                                        record['timestamp'] = int(time.mktime(dtime.timetuple()))

                                for field in remove:
					if record.has_key(field):
	                                	del record[field]

                                for field, value in record.items():
                                	if "." in field:
                                                tmplevel = combine( tmplevel,  build_arbo( field.split('.'), value) )
                                        else:
                                                newrecord[field] = value

                                metric = []
                                can_insert = True
                                if ( tmplevel.has_key('metric') ):
                                	for metricname, value in tmplevel['metric'].items():
						if record.has_key('override_metric') and record['override_metric']:
							value["metric"]	=	record['override_metric']
						else:
	                                        	value["metric"] = 	metricname
                                                if ( 'value' in value.keys() ) and value is not None:
                                                	metric.append(value)
                                                elif ( 'value' in value.keys() ):
                                                        can_insert = False
                                        newrecord['perf_data_array'] = metric
                                        del (tmplevel['metric'])

                                if ( len(tmplevel.keys()) > 0 ):
                                        newrecord = combine(newrecord, tmplevel)
				
                                incr = 0
                                if ( newrecord.has_key('metrics') ):
                                	while  ( incr < len(newrecord['metrics'] ) ) :
                                        	if ( not newrecord['metrics'][incr].has_key('value') or newrecord['metrics'][incr]['value'] == None ) :
                                                	newrecords['metrics'].pop(incr)
			for field, value in newrecord.items():
				if field in ['state','state_type']:
					newrecord[field]	=	int(float(value))
			newdata.append(newrecord)
                        if can_insert:
                               	inserted = amqp_bus.publish(json.dumps(newrecord), formatRoutingKey(record) )
                                if ( inserted ):
					cmpt += 1
                                        pass
                                else:
                                        record_fail.append({formatRoutingKey(record) : newrecord})
		resultats['data'] =  newdata

        else:
                # We report the records to a "pile" file to be executed when published
                newresultat = {}
                newdata = []
		for record in resultats['data']:
                	newrecord = {}
                        tmplevel = {}
                        remove = []
                        for field, value in record.items():
	                        if 'metric.' in field and  record.has_key( field.split('.')[1] ):
        	                        record[ str(field.split('.')[0])+"."+str(record[field.split('.')[1]])+"."+str(field.split('.')[2]) ] = value
                                        remove.append(field)

                                for field in remove:
                                        del record[field]

                                for field, value in record.items():
                                        if "." in field:
                                                tmplevel = combine( tmplevel,  build_arbo( field.split('.'), value) )
                                        else:
                                                newrecord[field] = value

                                metric = []
                                can_insert = True
                                if ( tmplevel.has_key('metric') ):
                	                for metricname, value in tmplevel['metric'].items():
                        	                value["metric"] = metricname
                                                if ( 'value' in value.keys() ) and value is not None:
                                                	metric.append(value)
                                                elif ( 'value' in value.keys() ):
                                                        can_insert = False
                                        newrecord['perf_data_array'] = metric
                                        del (tmplevel['metric'])
                                if ( len(tmplevel.keys()) > 0 ):
                                	newrecord = combine(newrecord, tmplevel)

			newdata.append(newrecord)

                        if can_insert:
                               	inserted = amqp_bus.publish(json.dumps(newrecord), formatRoutingKey(record) )
                                if ( inserted ):
                                      	pass
                                else:
                                        # We directly go to the temp file
                                        record_fail.append({formatRoutingKey(record) : newrecord})
		resultats['data'] =  newdata

        recordFailedBusPublication(record_fail)
	print len(resultats['data']), " records with ",len(record_fail)," failed"
        return resultats

def publishInCanopsis( resultats, settings, params, args ):
	newdata	=	{}
	for src,data in resultats.iteritems():
		if data.has_key('data'):
			newdata[src]	=	publishInCanopsisSource( data, settings, params, args )
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
        if ( params.has_key('idstk') ):
                idstk = params['idstk']

        settings        =       candles.getConfigDatabase(instance)
        db              =       bibsql.sqldb(conf=settings)

        for key,source in resultats.iteritems():
                if source.has_key('data') and source['data']:
                        for record in source['data']:
                                fieldidvalue = record[fieldid]
                                dtsync = datetime.now()
                                str1 = "UPDATE %s set dtsync=NOW() where %s=%s and idstk=%s" % (table, fieldid, fieldidvalue, idstk )
                                r = db.update(str1)
                                db.commit()

        return resultats

