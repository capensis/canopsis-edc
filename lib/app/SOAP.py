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

# We implement the JSON libraries
import sys
import os

# We add the suds lib
sys.path.append( os.environ['EDC_HOME']+"/lib/python2.7/site-packages/suds-0.4-py2.7.egg")

#import settings
import xml.etree.cElementTree as et
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.transport.http import HttpAuthenticated
from edc_lib import candles
import logging

from Base import Base

class UnicodeFilter(MessagePlugin):
    def received(self, context):
        decoded = context.reply.decode('utf-8', errors='ignore')
        reencoded = decoded.encode('utf-8')
        context.reply = reencoded

class SOAP (Base):

	def __init__(self):
		pass

	def convert_to_json(self):
		data = False
		url  = False
		params = { }

		if self.file.has_key('serv'):
			params['service'] = self.file['serv']

                if self.file.has_key('port'):
                        params['port'] = self.file['port']

			
                if self.file.has_key('url'):
                        params['location'] = self.file['url']
	
		if self.file.has_key('httpAuth.username') and self.file.has_key('httpAuth.password'):
			tmp	=	{'username' : self.file['httpAuth.username'], 'password' : self.file['httpAuth.password'] }
			params['transport'] = HttpAuthenticated( **tmp )

                if self.file.has_key('proxy') and self.file['proxy']:
			proxies = {}
	                for method,prox in self.file['proxy'].iteritems():
        	                if url and url.startswith('http')==False:
                	                proxies[method] = "%s://%s" % (method,prox)
                        	else:
                                	proxies[method] = prox
			params['proxy'] = proxies

		if ( self.file.has_key('wsdl' ) ):
			wsdl = self.file['wsdl']
 
		params['plugins'] = [UnicodeFilter()]
		
		client = Client(wsdl, **params)

		if self.file.has_key('username') and self.file.has_key('password'):
			token 		=	client.factory.create('AuthToken')
			token.username	=	self.file['username']
			token.password	=	self.file['password']
			client.set_options(soap_headers=token)

		if self.file.has_key('function') and self.file['function']:
			tmp	=	{}
			for key, value in self.file.iteritems():
				if 'params.' in key:
					tmp[key[len('params.'):]] = value
			if len(tmp):
				result = getattr(client.service, self.file['function'])(**tmp)
			else:
				result = getattr(client.service, self.file['function'])
		if ( type(result) == list ):	
			try:
				f = ''.join(result)
				if self.file.has_key('encode_origin'):
					try:
						f = f.encode(self.file['encode_origin'],'strict')
					except Exception as e:
						self.message.addError('ETC_ERR_ENCODING', self.file['encode_origin'], 'utf-8', e)
				else :
					encode = 'utf-8'
					try:
						f = f.encode(encode)
	                        	except Exception as e:
        	                        	self.message.addError('ETC_ERR_ENCODING', 'utf-8', 'utf-8', e)
			
				tmp_file = "tmp_soap.xml"
				candles.writeInFile(f,tmp_file)
				tree = et.parse(tmp_file)
				root = tree.getroot()

				data = []
				tmp = {}
				for elt in root:
					tmp[elt.tag] = elt.text
				data.append(tmp)
				os.remove(tmp_file)
			except Exception as e:
				self.message.addError('ETC_ERR_STEP', 'Response treatment failure %s' %e )
		else :
			data = []
			data.append( { 'result': result } ) 


        	return data

        # returns the datas from the source
        def getDataSOAP(self):
                results = { }
		if self.conf:
                        file            =       self.conf
                        self.file       =       file
                try:
                        self.query_name = self.file['name']
                except Exception as e:
                        self.message.addError('ETC_ERR_CONFIG',  "No name found for the file query : %s" % e)
                if ( self.file.has_key('mapping') ):
                        self.current_mapping = self.file['mapping']
                else:
                        self.current_mapping = {}
		try:
	               	self.result['data'] = self.convert_to_json()
                        self.content = ""
       	                self.treatData_generic()
               	        results = self.result
                       	self.result = {}
                       	self.current_file = {}
                except Exception as e:
                        self.message.addError('ETC_ERR_CONFIG', 'Impossible to find file in configuration : %s' % e)
                self.current_mapping = { }
                self.data = results


	def init(self):
		if self.conf.has_key('name'):
			self.name = self.conf['name']
		self.getData_generic()

        # returns the datas from the source
        def getData(self):
                self.getDataSOAP()

