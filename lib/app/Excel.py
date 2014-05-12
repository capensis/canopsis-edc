#!/opt/connecteurSQL/bin/python2.7
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
import xlrd
from Base import Base
import unicodedata

global log_dir
log_dir = os.environ['EDC_LOG']

# Lib for Messages
from app.Message import Message
global message
message = Message( log_dir )

# removes accents from string
def remove_accents(input_str):
	nkfd_form = unicodedata.normalize('NFKD', input_str)
	only_ascii = nkfd_form.encode('ASCII', 'ignore')
	return only_ascii

# Tries to convert a string into unicode
def try_unicode(string, errors='strict'):
        """
        Tries to convert a string into unicode
        """
        encoding_guess_list = ["utf-8","ascii","cp1250", "latin1", "iso-8859-2","iso-8859-1","utf-16"]
        if isinstance(string, unicode):
                return string
        assert isinstance(string, str), repr(string)
        for enc in encoding_guess_list:
                try:
        	        return string.decode(enc, errors)
                except UnicodeError, exc:
                        continue

class Excel (Base):

	def __init__(self):
		pass

	# done in getData
	def convert_to_json(self):
		data 	=	self.data
		return data

	def init(self):
		if self.conf.has_key('name'):
			self.name = self.conf['name']
		self.getData_generic()

        # returns the datas from the source
        def getData(self):

                results = {}
                if self.conf:
			workbook	=	""
                        self.file 	= 	self.conf
			file		=	self.conf
			self.result	=	{}
			self.result['data']	=	[]

                        if self.file.has_key("encode_origin"):
                                self.encode_orig 	= 	self.file["encode_origin"]
                        else:
				# the standard excel encoding
                                self.encode_orig 	= 	"iso-8859-1"

                        try:
                                self.query_name 	= 	file['name']
                        except Exception as e:
                                message.addError('022',  "No name found for the file query : %s" % e, 2)

                        if ( file.has_key('mapping') ):
                                self.current_mapping 	= 	file['mapping']
                        else:
                                self.current_mapping 	= 	{}

			# retrieve the excel document
                        if ( (file.has_key("dynamic") and file["dynamic"]) or (file.has_key("url") and file["url"]) ) :
                                if file.has_key("dynamic") and file["dynamic"]:
                                        if len(self.args) and file.has_key("param_name"):
                                                for arg in self.args:
							tmp_arg = arg.split("=")
							if len(tmp_arg) == 1:
	                                                        tmp_arg = arg.split(":")
                                                        if tmp_arg[0] == file["param_name"]:
                                                                try:
                                                                        self.filename 	= 	tmp_arg[1]
									workbook       = 	xlrd.open_workbook(self.filename)
                                                                except Exception as e:
                                                                        message.addError('ETC_ERR_STEP', 'Impossible to load file defined in configuration', e)
                                                                break
                                        else:
                                                message.addError('ETC_ERR_STEP', 'Impossible to match the call with the configuration')
                                else:
                                        try:
                                        	self.filename 	= 	file['url']
						workbook       	=       xlrd.open_workbook(self.filename)
                                        except Exception as e:
                                        	message.addError('ETC_ERR_STEP', 'Impossible to load file defined in configuration', e)

				

				# we can only process one sheet at a time
                                if workbook and file.has_key("sheet") and file['sheet']:

					#print workbook.sheet_names()

					worksheet 	= 	workbook.sheet_by_name(file['sheet'])
                                        num_rows 	= 	worksheet.nrows - 1
                                        num_cells 	= 	worksheet.ncols - 1
                                        curr_row 	= 	-1

					# Header
					column_list	=	[]
					columns		=	[]

					# We retrieve the columns asked / all if empty
					if file.has_key("column_list") and file['column_list']:
						file['column_list']	=	file['column_list'].split(',')
						for col in file['column_list']:
							col = col.lower()
							if len(col) == 1:
								col_number	=	ord(col) - 96 - 1
								column_list.append(col_number)
							elif len(col) == 2:
								col_number	=	( ( ord(col[0]) - 96 ) * 26 ) + ( ord(col[1]) - 96 ) - 1
								column_list.append(col_number)
							elif len(col) > 2 and col.find('-')!=-1:
								tmp		=	col.split('-')
								if len(tmp) == 2:
									start	=	tmp[0].lower()
                        			                        if len(start) == 1:
                                                			        start	=	ord(start) - 96 - 1
                        			                        elif len(start) == 2:
                                                			        start   =	( ( ord(start[0]) - 96 ) * 26 ) + ( ord(start[1]) - 96 ) - 1
                                                                        end	=	tmp[1].lower()
                                                                        if len(end) == 1:
                                                                                end   	=       ord(end) - 96 - 1
                                                                        elif len(end) == 2:
                                                                                end   	=       ( ( ord(end[0]) - 96 ) * 26 ) + ( ord(end[1]) - 96 ) - 1
									column_list.extend([i for i in range(start,end+1)])
			
					else:
						column_list	=	[i for i in range(num_cells)]

					# We order the columns
					column_list.sort()
		
					# We name the columns
					if file.has_key("column_names") and file['column_names']:
						file['column_names']     =       file['column_names'].split(',')
						if isinstance ( file['column_names'], int ):
							curr_row 	= 	file['column_names']
							row 		= 	worksheet.row(curr_row)
                		                        curr_cell 	= 	-1
                        		                while curr_cell < num_cells:
                                		        	curr_cell 	+= 	1
								if curr_cell in column_list:
		                                                	cell_value 	= 	worksheet.cell_value(curr_row, curr_cell)
									try:
										columns.append(cell_value)
									except Exception as e:
										columns.append(remove_accents(try_unicode(cell_value)))
						else:
							columns 	=	file['column_names']

					# We set the cursor to the first line asked
					if file.has_key("start_line") and file['start_line']:
						curr_row	=	int(float(file['start_line']))-2
	
					# Values
                                        while curr_row < num_rows:
						line		=	{}
                                        	curr_row 	+= 	1
                                                row 		= 	worksheet.row(curr_row)
                                                curr_cell 	= 	-1
                                                while curr_cell < num_cells:
                                                        curr_cell 		+= 	1
							if curr_cell in column_list:
	                                                        cell_value 		= 	worksheet.cell_value(curr_row, curr_cell)
								try:
									field_name	=	columns[column_list.index(curr_cell)]
								except:
									field_name	=	('field %s') % curr_cell
								line[field_name]	=	cell_value
						self.result['data'].append(line)

				else:
					pass

                                self.treatData_generic()	
				results			=	self.result
                                self.result		=	{}
                                self.current_file	=	{}
                        else :
                                message.addError('ETC_ERR_STEP', 'Impossible to find file in configuration', 2)

                        self.current_mapping = { }

                self.data = results

