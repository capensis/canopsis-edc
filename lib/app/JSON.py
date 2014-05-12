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

from Base import Base

#import settings
import simplejson as json
from edc_lib.candles import getJsonToArray

class JSON (Base):

	def __init__(self):
		pass

	def init(self):
		if self.conf.has_key('name'):
			self.name = self.conf['name']
		self.getData_generic()


        def convert_to_json(self):
                return getJsonToArray(self.filename)

        # returns the datas from the source
        def getData(self):
		self.getDataFile()        

