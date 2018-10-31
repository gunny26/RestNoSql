from distutils.core import setup, Extension
#from Cython.Build import cythonize
import sys, string, os
import shutil

args = {"name": "RestNoSql",
        "author": "Arthur Messner",
        "author_email": "arthur.messner@gmail.com",
        "description": "NoSQL Database with Rest Interface and Python Client Dict Class",
        "url" : "https://github.com/gunny26/RestNoSql",
        "long_description": __doc__,
        "platforms": ["any", ],
        "license": "LGPLv2",
        "packages": ["RestNoSqlClient"],
        # "scripts": ["bin/wstar.py"],
        # Make packages in root dir appear in pywbem module
        "package_dir": {
            "RestNoSqlClient": "client",
            },
        # Make extensions in root dir appear in pywbem module
        #"ext_package": "webstorage",
        # "ext_modules" : cythonize("*.pyx"),
        "requires" : ["requests", ],
        "version" : "0.1.0",
        }
setup(**args)
