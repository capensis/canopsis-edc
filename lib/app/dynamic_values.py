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

import string
import random

def borne ( value , record):
	if value.has_key('test_value') and record.has_key( value['test_value'] ):
		myvalue = record[ value['test_value'] ]
		if value['function'].has_key('min'):
			if not myvalue > value['function']['min']:
				return value['false_value']
		if value['function'].has_key('max'):
			if not myvalue < value['function']['max']:
				return value['false_value']
		
	else:
		return value['unknown_value']
	return value['true_value']

def random_string (value, record):
	chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
	if ( not value["function"].has_key('size') ):
		value["function"]['size'] = 10
	return ''.join(random.choice(chars) for x in range(value["function"]["size"]))

def concat ( value, record):
	values_to_concat = []
	if ( value['function'].has_key('fields_values') and isinstance(value['function']['fields_values'],  list) ):
		for fname in value['function']['fields_values']:
			if record.has_key(fname) and set(record[fname]).issubset(['',False,' ']) == False:
				values_to_concat.append( record[fname] )
	if ( value['function'].has_key('constants_values') and isinstance(value['function']['constants_values'], list) ) :
			values_to_concat += value['function']['constants_values']
	
	if ( value['function'].has_key('delimiter') ):
		delimiter = value['function']['delimiter']
	else:
		delimiter = '_'
	return delimiter.join(values_to_concat)

def replace( value, record):
	if ( value['function'].has_key('value_to_replace') and value['function'].has_key('field_name') and value['function'].has_key('replace_value')):
		if ( record[value['function']['field_name']] == value['function']['value_to_replace'] ):
			return value['function']['replace_value']
		else: 
			return record[value['function']['field_name']]		

	elif ( value['function'].has_key('field_name') ):
		return record[value['function']['field_name']]		
	else:
		return ''

def substring ( value, record):
	if value['function'].has_key('source') and (value['function'].has_key('start') or value['function'].has_key('length') or value['function'].has_key('end')):
		start	=	None
		end	=	None
		
		if value['function']['start']:
			start	=	int(float(value['function']['start']))
		
                if value['function']['length'] and not value['function']['end']:
                        end   	=       int( start + int(float(value['function']['length'])))
		elif value['function']['end']:
                        end     =       int(float(value['function']['end']))

		return record[value['function']['source']][start:end]
		
