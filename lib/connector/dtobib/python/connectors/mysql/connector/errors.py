# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009, 2012, Oracle and/or its affiliates. All rights reserved.

# MySQL Connector/Python is licensed under the terms of the GPLv2
# <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>, like most
# MySQL Connectors. There are special exceptions to the terms and
# conditions of the GPLv2 as it is applied to this software, see the
# FOSS License Exception
# <http://www.mysql.com/about/legal/licensing/foss-exception.html>.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""This module implements Exception classes
"""

import logging

import utils
import errorcode
from locales import get_client_error

logger = logging.getLogger('myconnpy')

# See get_mysql_exceptions function for errno ranges and smaller lists
_PROGRAMMING_ERRORS = (
    1083, 1084, 1089, 1090, 1091, 1093, 1096, 1097, 1101, 1102, 1103, 1107,
    1108, 1110, 1111, 1113, 1120, 1124, 1125, 1128, 1136, 1366, 1139, 1140,
    1146, 1149, 1426)
_OPERATIONAL_ERRORS  = (
    1028, 1029, 1030, 1053, 1077, 1078, 1079, 1080, 1081, 1095, 1104, 1106,
    1114, 1116, 1117, 1119, 1122, 1123, 1126, 1133, 1135, 1137, 1145, 1147,)

def get_mysql_exception(errno, msg, sqlstate=None):
    """Get the exception matching the MySQL error number
    
    This function will return an exception based on the errno. The given
    message will be passed on in the returned exception.
    
    Returns an Error-object.
    """
    exception = OperationalError
    
    if (1046 <= errno <= 1052) or (1054 <= errno <= 1061) or \
       (1063 <= errno <= 1075) or errno in _PROGRAMMING_ERRORS:
        exception = ProgrammingError
    elif errno in (1109, 1118, 1121, 1138, 1292):
        exception = DataError
    elif errno in (1031, 1112, 1115, 1127, 1148, 1275):
        exception = NotSupportedError
    elif errno in (1062, 1082, 1099, 1100):
        exception = IntegrityError
    elif errno in (1085, 1086, 1094, 1098):
        exception = InternalError
    elif (1004 <= errno <= 1030) or (1132 <= errno <= 1045) or \
         (1141 <= errno <= 1145) or (1129 <= errno <= 1133) or \
         errno in _OPERATIONAL_ERRORS:
        exception = OperationalError
    
    return exception(msg, errno=errno,sqlstate=sqlstate)

def get_exception(packet):
    """Returns an exception object based on the MySQL error
    
    Returns an exception object based on the MySQL error in the given
    packet.
    
    Returns an Error-Object.
    """
    errno = errmsg = None
    
    if packet[4] != '\xff':
        raise ValueError("Packet is not an error packet")
    
    try:
        packet = packet[5:]
        (packet, errno) = utils.read_int(packet, 2)
        if packet[0] != '\x23':
            # Error without SQLState
            errmsg = packet
        else:
            (packet, sqlstate) = utils.read_bytes(packet[1:], 5)
            errmsg = packet
    except Exception, err:
        return InterfaceError("Failed getting Error information (%r)" % err)
    else:
        return get_mysql_exception(errno, errmsg, sqlstate)

class Error(StandardError):
    """Exception that is base class for all other error exceptions"""
    def __init__(self, msg=None, errno=None, values=None, sqlstate=None):
        self.msg = msg
        self.errno = errno or -1
        self.sqlstate = sqlstate
        
        if not self.msg and (2000 <= self.errno < 3000):
            errmsg = get_client_error(self.errno)
            if values is not None:
                try:
                    errmsg = errmsg % values
                except TypeError, err:
                    errmsg = errmsg + " (Warning: %s)" % err
            self.msg = errmsg
        elif not self.msg:
            self.msg = 'Unknown error'
        
        if self.msg and self.errno != -1:
            if self.sqlstate:
                self.msg = '%d (%s): %s' % (self.errno, self.sqlstate,
                                            self.msg)
            else:
                self.msg = '%d: %s' % (self.errno, self.msg)
    
    def __str__(self):
        return self.msg
        
class Warning(StandardError):
    """Exception for important warnings"""
    pass

class InterfaceError(Error):
    """Exception for errors related to the interface"""
    pass

class DatabaseError(Error):
    """Exception for errors related to the database"""
    pass

class InternalError(DatabaseError):
    """Exception for errors internal database errors"""
    pass

class OperationalError(DatabaseError):
    """Exception for errors related to the database's operation"""
    pass

class ProgrammingError(DatabaseError):
    """Exception for errors programming errors"""
    pass

class IntegrityError(DatabaseError):
    """Exception for errors regarding relational integrity"""
    pass

class DataError(DatabaseError):
    """Exception for errors reporting problems with processed data"""
    pass

class NotSupportedError(DatabaseError):
    """Exception for errors when an unsupported database feature was used"""
    pass

