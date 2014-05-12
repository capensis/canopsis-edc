#!/usr/bin/env python

# Init the treatment on the webservice call
"""
We get the source called by a webservice in a POST var
"""

# We import the CGI library for HTTP vars
import cgi

# We import our methods
import key

def start_car (source=False, args=False, search=False) :
	form		=	cgi.FieldStorage()
	# If there are vars:
	if source != False and args != False:
		# We launch the fonction with present datas
		return key.processRefresh(source,args)
	elif source != False:
		# We launch the function
		return key.processRefresh(source)
	else:
		# We return available methods
		return key.allMethods(search)

# End of motor.py
