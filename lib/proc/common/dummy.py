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
from edc_lib import candles
from connector import bibsql
from app.Message import Message
import datetime

global base
base = os.environ['EDC_HOME']
global log_dir
log_dir = os.environ['EDC_LOG']
global message
message = Message( log_dir )

def output(data, conf, params, args):
	if data:
	        for name,result in data.iteritems():
			if 'data' in result.keys() and len(result['data'])>0:
	                	for row in result['data']:
        		                print ';'.join(row.keys())
                		        break
	                	for row in result['data']:
        	                	print ';'.join([str(x) for x in row.values()])
        return data

