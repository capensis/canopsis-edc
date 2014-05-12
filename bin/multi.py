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

import sys
import os
#We import library path

def getConfig(file):
        try:
		import ConfigParser
                Config = ConfigParser.ConfigParser()
                Config.read(file)
                return Config
        except:
                return False

def ConfigSectionMap(section,Config):
        tmp             =       {}
        options         =       Config.options(section)
        for option in options:
                try:
                        tmp[option]     =       Config.get(section, option)
                except:
                        tmp[option]     =       None
        return tmp

# The current path
dir_path	=	os.path.dirname(os.path.abspath(__file__))
main_cfg	=	"%s/../cfg/ref/main.cfg" % ( dir_path )
try:
	config	=	getConfig(file=main_cfg)
	conf	=	ConfigSectionMap("edc",config)
except:
	conf	=	{}

#we find cur dir
if not os.environ.has_key('EDC_HOME') or os.environ['EDC_HOME'] == '' or (conf.has_key('edc_home') and conf['edc_home'] != os.environ['EDC_HOME']):
	if conf.has_key('edc_home'):
		os.environ['EDC_HOME']  =       conf['edc_home']
	else:
	        dir_path                =       os.path.dirname(os.path.abspath(__file__))
        	edc_home                =       "%s/.." % dir_path
	        os.environ['EDC_HOME']  =       edc_home

sys.path.append(os.environ['EDC_HOME']+"/lib")
sys.path.append(os.environ['EDC_HOME']+"/lib/python2.7")
sys.path.append(os.environ['EDC_HOME']+"/lib/proc")
sys.path.append( os.environ['EDC_HOME']+"/lib/python2.7/site-packages")

sys.path = list(set(sys.path))


if ( conf.has_key('var_dir') ):
	os.environ['EDC_VAR']	=	conf['resources_dir']
else:
	os.environ['EDC_VAR']	=	os.environ['EDC_HOME']+"/var"

if ( conf.has_key('log_dir') ):
	os.environ['EDC_LOG']	=	conf['log_dir']
else:
	os.environ['EDC_LOG']	=       os.environ['EDC_HOME']+"/log"

os.environ['PYTHON_EGG_CACHE'] 	=	os.environ['EDC_HOME']

rerun	=	0

if not os.name in [ "nt", "dos" ]:
	if conf.has_key('ld_library_path') and (not os.environ.get('LD_LIBRARY_PATH') or os.environ['LD_LIBRARY_PATH'] != conf['ld_library_path']):
        	os.environ['LD_LIBRARY_PATH']   =       conf['ld_library_path']
	        rerun                           +=      1
	if conf.has_key('pythonpath') and (not os.environ.get('PYTHONPATH') or os.environ['PYTHONPATH'] != conf['pythonpath']):
        	os.environ['PYTHONPATH']        =       conf['pythonpath']
	        rerun                           +=      1
	if conf.has_key('path') and (not os.environ.get('PATH') or os.environ['PATH'] != conf['path']):
        	os.environ['PATH']              =       conf['path']
	        rerun                           +=      1
	if rerun > 0 and os.environ.has_key('EDC_RUN_MULTI') == False:
        	os.environ['EDC_RUN_MULTI']     =       "True"
	        runpy                           =       "%s/bin/run_multi.py" % os.environ['EDC_HOME']
        	os.execvpe(runpy, sys.argv, os.environ)

if sys.version_info < (2, 7):
	print "ERROR : You must use a Python superior or equal to 2.7"
else:
        try:
                from edc_lib import key
                if len(sys.argv) > 1 and sys.argv[1]:
                        list_src        =       key.getAllMotorsToStart(sys.argv[1])
                        if list_src:
                                from edc_lib import motor
                                result  =       False
                                for src in list_src:
                                        for key, args in src.iteritems():
                                                if key != 'general':
                                                        try:
                                                                print '##################################'
                                                                print "%s %s" % (key, ' '.join(args['args']))
                                                                print '##################################'
                                                                if key and len(args['args']):
                                                                        """  We have more than one argument """
                                                                        result = motor.start_car ( key, args['args'] )
                                                                elif key:
                                                                        """ We have one argument => source """
                                                                        result = motor.start_car( key )
                                                        except Exception:
                                                                print "ERROR : %s could not be executed" % (key)
                        else:

                                list_available_sources  =       key.allMethodsMulti()

                else:
                        list_available_sources  =       key.allMethodsMulti()
        except Exception:
                print Exception
                print "ERROR : I could not execute the program properly"

# End start.py
