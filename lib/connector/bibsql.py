#!/opt/connecteurSQL/bin/python2.7
# -*- coding: utf-8 -*-
'''
Created on 26 juil. 2012
@author: bbelarbi
'''
import os
import biblog
import bz2

import connectors.mysql.connector
import connectors.mysql.connector.errors
import sys
import datetime, decimal
from app.Message import Message

global log_dir
log_dir = os.environ['EDC_LOG']
global message
message = Message( log_dir )

"""
RECODE_TYPES = {
        cx_Oracle.BINARY: str,
        cx_Oracle.LONG_BINARY: str,
        cx_Oracle.LOB: str,
        cx_Oracle.BLOB: str,
        cx_Oracle.CLOB: str,
        cx_Oracle.NCLOB: unicode,
        cx_Oracle.STRING: str,
        cx_Oracle.FIXED_CHAR: str,
        cx_Oracle.LONG_STRING: str,
        cx_Oracle.DATETIME: datetime.datetime,
        cx_Oracle.TIMESTAMP: datetime.datetime,
        cx_Oracle.NUMBER: decimal.Decimal,
        cx_Oracle.NATIVE_FLOAT: float,
        cx_Oracle.INTERVAL: int,
    }
"""

def is_array(var):
    return isinstance(var, (list, tuple))

class Descriptor(object):
    attrs = ['name', 'type', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok']
    def __init__(self,values):
        for idx,attr in enumerate(self.attrs):
            self.__dict__[attr] = None
            if is_array(values):
                self.__dict__[attr] = values[idx]
            else:
		message.addError("ETC_ERR_DATABASE", "Error Type : %s" % type(values))
    def __str__(self):
        return repr([self.__dict__[attr] for attr in self.attrs ])

def deCryptPassWord(passw,isCrypted):
    import base64
    if isCrypted == "True":
        return base64.b64decode(passw)
    return passw

def enCryptPassWord(passw):
    import base64
    return base64.b64encode(passw)

class BibSql(object):
    '''
    classdocs
    '''
    conn = None
    curs = None
    description = None
    DIC = "DIC"
    STR = "STR"
    NUM = "NUM"

    def __init__(self,dbconfig=None,method=None,conf=None):
        '''
        Constructor
        '''
        if conf:
            cnf = conf
	    for key, value in cnf.iteritems():
		tmp		=	[x for x in value.split('\\') if x]
	    	newval		=	'\\'.join(tmp)
		cnf[key]	=	newval
        else:
            if dbconfig and method:
                cnf = dbconfig[method]
            else:
                biblog.bibMsgRaise(cdmsg="CONNECTION_ERROR")
        try:
            if cnf['dbtype'] == 'MSSQL' or cnf['dbtype'] == 'PostgreSQL':
		try:
			import pypyodbc
		except Exception as e:
			sys.path.append("%s/lib/python2.7/site-packages/pypyodbc-1.2.0-py2.7.egg" % os.environ['EDC_HOME'])
			import pypyodbc
		try:
			if cnf['dbtype'] == 'MSSQL':
				self.conn = pypyodbc.connect('DRIVER=MSSQL;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=8.0;' % ( cnf['host'], cnf['port'], cnf['sid'], cnf['user'], cnf['password'] ) )
			elif cnf['dbtype'] == 'PostgreSQL':
				self.conn = pypyodbc.connect('DRIVER=PostgreSQL;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=8.0;' % ( cnf['host'], cnf['port'], cnf['sid'], cnf['user'], cnf['password'] ) )
		except Exception as e:
			try:
				dir_path = os.path.dirname(os.path.abspath(__file__))
				self.prev_ld_library_path = os.environ['LD_LIBRARY_PATH']
				os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH']+":"+dir_path+"/../../lib"
				if cnf['dbtype'] == 'MSSQL':
					self.conn = pypyodbc.connect('DRIVER=MSSQL;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=8.0;' % ( cnf['host'], cnf['port'], cnf['sid'], cnf['user'], cnf['password'] ) )
				elif cnf['dbtype'] == 'PostgreSQL':
					self.conn = pypyodbc.connect('DRIVER=PostgreSQL;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=8.0;' % ( cnf['host'], cnf['port'], cnf['sid'], cnf['user'], cnf['password'] ) )
			except Exception as e:
				message.addError("ETC_ERR_DATABASE", "Connection KO", e )

	    elif cnf['dbtype'] == "ORACLE":
		os.environ["NLS_LANG"] = ".AL32UTF8"
		try:
	                import cx_Oracle
		except Exception as e:
			dir_path = os.path.dirname(os.path.abspath(__file__))
			sys.path.append("%s/dtobib/python/connectors/cx_Oracle-5.1" % dir_path)
			import cx_Oracle	

		if ( not cnf.has_key('crypted') ) :
			cnf['crypted'] = False
                self.conn = cx_Oracle.connect(cnf['user'], deCryptPassWord(str(cnf['password']),str(cnf['crypted'])) , cnf['host']+':'+cnf['port']+'/'+cnf['sid'])
            elif cnf['dbtype'] == "MYSQL":
                myport = cnf['port']
                try:
                    myport = int(myport)
                except ValueError:
                    myport = 3306
                
                config = {
                    'host' : str(cnf['host']),
                    'port' : int(cnf['port']),
                    'unix_socket' : None,
                    'user' : str(cnf['user']),
                    'password' : deCryptPassWord(str(cnf['password']),str(cnf['crypted'])),
                    'database' : str(cnf['sid'])
                    }
                self.conn = connectors.mysql.connector.connect(**config)

        except connectors.mysql.connector.errors.InterfaceError, e:
            biblog.bibMsgRaise(cdmsg="CONNECTION_ERROR",params=["MYSQL",cnf["sid"],method])
        
        if self.conn != None:
            self.curs = self.conn.cursor()
        else:
	    message.addError("ETC_ERR_DATABASE", "Connection KO" )

    def restaure_prev_environ_var(self):
	os.environ['LD_LIBRARY_PATH'] = self.prev_ld_library_path
	os.environ['PATH'] = self.prev_path

    def cmd(self,str1):
        try:
	    message.addMessage( "ETC_STEP_DATABASE",  "Executing : %s" % str1 )
       	    self.curs.execute(str1)
	    message.addMessage( "ETC_STEP_DATABASE",  "Query Executed" )
        except connectors.mysql.connector.errors.Error, e:
	    message.addError("ETC_ERR_DATABASE", "Could not execute the query",  e )
            return
        
    def commit(self):
        self.conn.commit()

    def select(self,str1,numRows=-1,retType=DIC):
	encoding_guess_list = ["utf-8","ascii","cp1250", "latin1", "iso-8859-2","iso-8859-1","utf-16"]
	try:
	        self.curs.execute(str1)
	except Exception as e:
		try:
			s1      =       str1
                        s2      =       str1
			cmpt	=	0
                        try:
				for enc in encoding_guess_list:
					try:
						s2 = s1.decode(enc)
						self.curs.execute(s2)
						cmpt    += 1
						break
					except Exception as e:
						try:
							s2 = s2.encode('utf-8')
                                                        self.curs.execute(s2)
							cmpt    += 1
                                                        break
                                                except Exception as e:
							try:
	                                                        s2 = s2.encode(enc)
        	                                                self.curs.execute(s2)
                	                                        cmpt    += 1
							except Exception as e:
								pass
				if cmpt == 0:
					message.addError("ETC_ERR_DATABASE", "Could not execute the query",  e )
                        except Exception as e:
				pass
		except Exception as e:
			message.addError("ETC_ERR_DATABASE", "Could not execute the query",  e.errmsglong )

        self.description =[Descriptor(i) for i in self.curs.description]
        res=None
        if numRows==-1 :
            res = self.curs.fetchall()
        else:
            res = self.curs.fetchmany(numRows)
        if retType==self.STR:
            if len(res)==1 :
                if len(res[0]) == 1:
                    return str(res[0][0])
            return "ERROR"
        elif retType==self.NUM:
            if len(res)==1 :
                if len(res[0]) == 1:
                    try:
                        return int(res[0][0])
                    except ValueError as e:
			message.addError("ETC_ERR_DATABASE", "Error",  e )
            return -1
        #elif retType==self.DIC:
        #        return res

        return self.rows_to_dict_list(res)

    def update(self, str1):
	return self.conn.cmd_query(str1)

    def rows_to_dict_list(self,rows):
        columns = [i[0] for i in self.curs.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def export2csv(self,stmt,filename):
        import csv
        self.curs.execute(stmt)
        self.description =[Descriptor(i) for i in self.curs.description]
        res = self.curs.fetchall()
        dump_writer = csv.writer(open(filename,'w'), delimiter='|',quotechar="'")
        dump_writer.writerow([i[0] for i in self.curs.description])
        for record in res:
            dump_writer.writerow(record)

    def nullify(self,L):
        """Convert empty strings in the given list to None."""
        # helper function
        def f(x):
            if(x == ""):
                return None
            else:
                return x
            
        return [f(x) for x in L]
    
    def importcsv(self, table, filename):
        import csv
        """
        Open a csv file and load it into a sql table.
        Assumptions:
         - the first line in the file is a header
        """
    
        f = csv.reader(open(filename))
        
        header = f.next()
        numfields = len(header)
    
        query = self.buildInsertCmd(table, numfields)
        self.curs.execute('SET foreign_key_checks = 0')
        for line in f:
            vals = self.nullify(line)
            self.curs.execute(query, vals)
        self.curs.execute('SET foreign_key_checks = 1')
        self.commit()
        return
    
    def buildInsertCmd(self,table, numfields):
        """
        Create a query string with the given table name and the right
        number of format placeholders.
        example:
        >>> buildInsertCmd("foo", 3)
        'insert into foo values (%s, %s, %s)' 
        """
        assert(numfields > 0)
        placeholders = (numfields-1) * "%s, " + "%s"
        query = ("insert into %s" % table) + (" values (%s)" % placeholders)
        return query

    def get_table_list(self):
        self.curs.execute("SHOW TABLES")
        return [ table for table, in self.curs ]
    
    
    def get_table_schema(self, table):
        self.curs.execute("SHOW CREATE TABLE %s" % (table))
        return self.curs.fetchone()[1]+";"
    
    def get_structure_sql(self):
        self.curs.execute("SET OPTION SQL_QUOTE_SHOW_CREATE=1")
        schemas = {}
        for table in self.get_table_list():
            schemas[table] = self.get_table_schema( table)
        
        return schemas
    
    def get_db_name(self):
        self.curs.execute("SELECT DATABASE()")
        return self.curs.fetchone()[0]
    
    def dump_structure_sql(self):
        print "#"
        print "# Dumping schema for database", self.get_db_name()
        print "#"
        print
        print
    
        for table, create_def in self.get_structure_sql().iteritems():
            print "#"
            print "# Table structure for table for table ", table
            print "#"
            print "DROP TABLE IF EXISTS ","`"+table+"`",";"
            print 
            print create_def
            print
            print
    def dump_sql(self):
        print "#"
        print "# Dumping schema for database", self.get_db_name()
        print "#"
        print
        print
        
        for table, create_def in self.get_structure_sql().iteritems():
            print "#"
            print "# Dumping schema for table", table
            print "#"
            print
            print create_def
            print
            print
            self.dump_data_sql(table)
        
        
    def get_column_names(self, table):
        self.curs.execute("DESCRIBE %s" % (table))
        return [ "`"+row[0]+"`" for row in self.curs ]
        
        
    def dump_data_sql(self, table):
        if is_array(table):
            for t in table:
                self.dump_data_sql(t)
            return
        print self.get_table_schema(table)
        colnames = self.get_column_names(table)
        colnames_sql = ', '.join(colnames)
        
        count = self.curs.execute("SELECT %s FROM %s" % (colnames_sql, table))
        
        if count == 0:
            return
        
        print "#"
        print "# Dumping data for table", table
        print "#"
        print
        print "INSERT INTO `%s`(%s) VALUES" % (table, colnames_sql)
        
        res = self.curs.fetchall()
        count = len(res)
        for index, row in enumerate(res):
            row_sql = " (%s)" % (', '.join(["'"+self.conn.converter.escape(str(r))+"'" for r in row]))
        
            if index < count-1:
                print row_sql ,
            else:
                print row_sql + ";"
        print
        print
        
    def close(self):
        if not self.conn == None :
            self.curs.close()
            self.conn.close()
        self.conn = None
        
    def __del__(self):
        self.close()
        
def sqldb(dbconfig=None,method=None,conf=None):
    return BibSql(dbconfig,method,conf)

# End bibsql.py
