#! /usr/bin/env python
#
# This file is only present so that the `compat/` directory is
# recognized as a Python package.
__docformat__ = 'reStructuredText'
__version__ = '$Revision$'



## main: run tests

if "__main__" == __name__:
    import doctest
    doctest.testmod(name="__init__")
