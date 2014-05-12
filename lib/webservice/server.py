#!/opt/connecteurSQL/bin/python2.7
import sys
import json
from bottle import route, get, run, request
import os

#### GET
# get all data source
@get('/get/data')
def get_all_data_sources():
        #to add motor library
        sys.path.append(os.environ['HOME']+'/smartengine/libs/')
        #motor pth
        import motor
	
	callback = request.params.get('callback', False) 
        output =   json.loads( motor.start_car( ))

	start = int( request.query.start ) or 0
	limit = int( request.query.limit ) or 20
	end   = start + limit

	filter = request.query.filter or False
	if ( filter ):
		filter = json.loads( filter )
		text = filter['$and'][0]['$or'][0]['source_description']['$regex']
		newoutput = []
		for record in output['data']:
			s_description = record['source_description']
			if ( s_description.count(text) > 0 ):
				newoutput.append(record)
		output['data'] = newoutput
		output['total'] = len(newoutput) 
			
	output['data'] = output['data'][start:end] 
	if ( not callback ) :
	        return output 
	else:
		return callback+'('+json.dumps( output ) +')'

# get all records
@get('/get/data/:id_source')
def get_all_records( id_source=None ):
        #to add motor library
        sys.path.append(os.environ['HOME']+'/smartengine/libs/')
        #motor pth
        import motor
	
	callback = request.params.get('callback', False) 

	output =  json.loads( motor.start_car(id_source) )
	if ( not callback ) :
	        return output
	else:
		return callback+'('+json.dumps( output ) +')'


@get('/get/data/:id_source/:filenames')
def get_all_records( id_source=None, filenames=None ):
        #to add motor library
        sys.path.append(os.environ['HOME']+'/smartengine/libs/')
        #motor pth
        import motor
	
	callback = request.params.get('callback', False) 
	arr_filenames = filenames.split(',')
	output =  json.loads( motor.start_car(id_source, arr_filenames) )
	if ( not callback ) :
	        return output
	else:
		return callback+'('+json.dumps( output ) +')'

run(host='0.0.0.0', port='5455')
