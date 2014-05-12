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
import xml.etree.cElementTree as et
from Base import Base

class XML (Base):

	def __init__(self):
		pass

	# recursively parse the DOM to retrieve the map
	def xml_map_recursive(self,el,cmpt):
		for elt in el:
                        if elt.tag and self.iterable==None:
				if self.iter.has_key(elt.tag)==False:
					self.iter[elt.tag] = []
                                self.iter[elt.tag].append(cmpt)
				cmpt += 1

			if elt.tag not in self.map and elt.tag != None:
                        	self.map.append(elt.tag)
                        else:
                                self.xml_map_recursive(elt,cmpt)
                        if elt.attrib:
                                for a,b in elt.attrib.iteritems():
                        	        tmp_map = "%s_%s" % (elt.tag,a)

	                        	if el.tag and self.iterable==None:
						if self.iter.has_key(tmp_map)==False:
							self.iter[tmp_map] = []
        	                        	self.iter[tmp_map].append(cmpt)
						cmpt+=1

                                        if tmp_map not in self.map and tmp_map != None:
                                 	       self.map.append(tmp_map)
		return

	# Return the XML structure
	def get_xml_map(self):
		cmpt = 0
                for el in et.fromstring(self.content):
			if el.tag and self.iterable==None:
				if self.iter.has_key(el.tag)==False:
					self.iter[el.tag] = []
				self.iter[el.tag].append(cmpt)
				cmpt += 1
			self.xml_map_recursive(el,cmpt)
		return

	# retrieve the iterable
	def get_iter(self):
		if self.iterable == None:
			curr_cmpt = 1000000000000
			for tag,arr in self.iter.iteritems():
				if len(arr)>=2:
					if arr[0]<curr_cmpt:
						self.iterable = tag
						curr_cmpt = arr[0]
		return

	# get content recursively
	def xml_content_recursive(self,el,line):
                for attr in el:
                	if line.has_key(attr.tag):
                        	self.line_result[attr.tag] = attr.text
			else:
				self.xml_content_recursive(attr,line)
                        if attr.attrib:
                                for a,b in attr.attrib.iteritems():
                        	        tmp_map = "%s_%s" % (attr.tag,a)
                                        if line.has_key(tmp_map):
                                 	       self.line_result[tmp_map] = b
		return

	# get the results
	def get_result_line(self):
		data = []	
                for attr in et.fromstring(self.content):
			def_val = ""
			line = {key: def_val for key in self.map}
			if attr.tag == self.iterable:
				self.xml_content_recursive(attr,line)
				data.append(self.line_result)
                        elif line.has_key(attr.tag):
                                self.line_result[attr.tag] = attr.text
                        else:
				for el in attr:
        		                self.xml_content_recursive(el,line)
					if self.line_result:
						data.append(self.line_result)
				self.line_result = {}
                return data

	# parse the xml and retrieve the data
	def convert_to_json(self):
		try:
			data = []
			self.map = []
			
			if self.file.has_key('item'):
				self.iterable = self.file['item']
			else:
				self.iterable = None

			self.iter = {}
			self.get_xml_map()

			self.get_iter()

			if self.iterable in self.map:
				self.map.remove(self.iterable)

			self.line_result = {}
			data = self.get_result_line()
			
		except Exception as e:
			self.message.addError('ETC_ERR_FORMAT', 'XML Data retrieval failure %s' % e)

        	return data

	def init(self):
		if self.conf.has_key('name'):
			self.name = self.conf['name']
		self.getData_generic()

        # returns the datas from the source
        def getData(self):
		self.getDataFile()  

