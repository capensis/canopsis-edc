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

#import settings
import simplejson as json
import csv
from edc_lib import candles
from Base import Base

class CSV (Base):

	def __init__(self):
		pass

	# returns csv file as a JSON dict
	def convert_to_json(self):

		if self.file.has_key('header') and self.file['header'] and self.file['header'].lower()!='false':
			fieldnames = self.file["header"].split(',')
	                try:
				if self.file.has_key('delimiter') and self.file['delimiter'] and self.file['delimiter'].lower()!='false':
	        	                csv_reader = csv.DictReader(open(self.filename,'rb'),fieldnames,skipinitialspace=True, delimiter=self.file['delimiter'])
				else:
					csv_reader = csv.DictReader(open(self.filename,'rb'),fieldnames,skipinitialspace=True)
                	except Exception as e:
                        	self.message.addError('ETC_ERR_FORMAT', 'CSV Data retrieval with header failure', e)
		else:
			try:
                                if self.file.has_key('delimiter') and self.file['delimiter'] and self.file['delimiter'].lower()!='false':
                                        reader = csv.DictReader(open(self.filename,'rb'), delimiter=self.file['delimiter'], skipinitialspace=True)
                                else:
                                        reader = csv.DictReader(open(self.filename,'rb'), skipinitialspace=True)
				fieldnames = []
				for row in reader:
					fieldnames = row
					break
				csv_reader.next()
                                if self.file.has_key('delimiter') and self.file['delimiter'] and self.file['delimiter'].lower()!='false':
                                        csv_reader = csv.DictReader(open(self.filename,'rb'),fieldnames,skipinitialspace=True, delimiter=self.file['delimiter'])
                                else:
                                        csv_reader = csv.DictReader(open(self.filename,'rb'),fieldnames,skipinitialspace=True)

        		except Exception as e:
				self.message.addError('ETC_ERR_FORMAT', 'CSV Data retrieval without header failure', e)
		try:
                        # We set the cursor to the first line asked
			start_line	=	0
                        if self.file.has_key("start_line") and self.file['start_line']:
				start_line	=	int(float(self.file['start_line']))

			if self.file.has_key('encode_origin') and self.file['encode_origin']:
				if self.file.has_key("start_line") and self.file['start_line']:
                                        i       =       0
                                        t       =       []
                                        for r in csv_reader:
                                                if i > start_line:
                                                        t.append(r)
                                                i       +=      1
					csv_reader	=	t
				data = json.loads(json.dumps([candles.dataDecodeEncode(r, 'ascii', self.file['encode_origin']) for r in csv_reader]))
			else:
				if self.file.has_key("start_line") and self.file['start_line']:	
					i	=	0
					t	=	[]
					for r in csv_reader:
						if i > start_line:
							t.append(r)
						i	+=	1
					csv_reader	=	t
				data = json.loads(json.dumps([r for r in csv_reader]))
        	except Exception as e:
			self.message.addError('ETC_ERR_FORMAT', 'Data structuration from CSV to Python failure', e)
        	return data

	# sets the name
	def init(self):
		if self.conf.has_key('name'):
			self.name = self.conf['name']
		self.getData_generic()

        # returns the datas from the source
        def getData(self):
		self.getDataFile()
