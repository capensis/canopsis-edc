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


import time
from datetime import datetime
from copy import deepcopy


def liveData2(data,conf,settings, args):
	results = []
	
        if data:
		for instance in data:
			for index in data[instance].keys():
				row = data[instance][index]
				if row.has_key('data') and row['data']:
					object = {}
					#for key in range(len(row['data'])):
					for key,value in enumerate(row['data']):
						if key == 0:
							for i,j in enumerate(value):
								split = j.split('.')
								if len(split)>1 and (split[1] == 'bunit' or split[1]=='type'):
									if object.has_key(split[0]) == False :
										object[split[0]] = {
											'bunit'		:	'',
											'metric'	:	split[0],
											'type'		:	'',
											'values'	:	[]
										}
									object[split[0]][split[1]] = value[j]

						for i,j in enumerate(value):
							if object.has_key(j) and j == object[j]['metric']:
								if value.has_key('timestamp'):
									ts = int(value['timestamp'])
								elif value.has_key('datetime'):
									dtime = datetime.strptime( value['datetime'], '%Y-%m-%d %H:%M:%S')
									ts = int(time.mktime(dtime.timetuple()))
									
								else :							
									ts = int(time.time())
								add_line = [ts,value[j]]
								object[j]['values'].append(add_line)
				if(object):
					for i in object.keys():
						results.append( { 'objet' : object[i] } )
		
	return results

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

def liveData(data, conf, params, args):
	results		=	[]
	
	tmpresults	=	{ }
	ts 		= time.time();
	i		=	0;
	if data:
		for instance in data:
			for index in data[instance].keys() :
				row = data[instance][index]
				if row.has_key('data') and row['data']:
					for record in row['data']:
						for fname, value in record.items():
							if 'metric.' in fname:
								if ( record.has_key( fname.split('.')[1]) ):
									metric = record[fname.split('.')[1]]
								else:
									metric = fname.split('.')[1]
								rk = "%s.%s.%s" % ( record['component'], record['resource'], metric )
								if fname.split('.')[2] != 'value':
									tmp = { fname.split('.')[2] : value }
									if tmpresults.has_key(rk):
										tmpresults[rk] = combine ( tmpresults[rk], tmp ) 
									else:
										tmpresults[rk] = tmp
								else:
									value_to_append = []
									if record.has_key("timestamp"):
										value_to_append.append( int( record['timestamp'] ) )
									elif record.has_key('datetime'):
										value_to_append.append( int( time.mktime( datetime.strptime( record['datetime'], '%Y-%m-%d %H:%M:%S').timetuple() )  ) )
									else:
										value_to_append.append( int(ts) )
									i = i+1

									value_to_append.append( value ) 
									
									if ( tmpresults.has_key(rk) ) :
										if ( tmpresults[rk].has_key('values') ):
											tmpresults[rk]['values'].append( value_to_append )
										else:
											tmp  = { 'values' : [ value_to_append ] } 
											tmpresults[rk] = combine( tmpresults[rk], tmp ) 
									else:
										tmpresults[rk] = { 'values' : [ value_to_append ] }

		

		for key, value in tmpresults.items():
			sorted(value['values'], key=lambda v: v[0]) 
			results.append( { 'objet': value } ) 

	return results

						
	
