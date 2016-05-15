#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# sudo zypper in python-setuptools
# http://docs.python.org/2/distutils/setupscript.html#installing-additional-files
#
import sys,os,glob,re

from distutils.core import setup
from setuptools.command.test import test as TestCommand

inkex_dir='/usr/share/inkscape/extensions'
sys.path.append(inkex_dir)        # gears-dev wants to import inkex.py
import importlib	
g = importlib.import_module('gears-dev')        # import 'gears-dev' as g

## Unfinished.

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)



setup(name='inkscape-gears-dev',
      version = g.__version__,
      description="Inkscape extension for generating gears. Development version.",
      author="Jürgen Weigert, et.al.",
      author_email="juewei@fabmail.org",
      url='https://github.com/jnweiger/inkscape-gears-dev',
      scripts=['gears-dev.py', 'gears-dev.inx', 'README.md'],
      license='GPL-2.0',
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Environment :: Console',
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
                  ],
      cmdclass={'test': PyTest},
      long_description="".join(open('README.md').readlines()),
      # tests_require=['pytest'],
      #packages=['inkscape-extensions-extra' ],
      install_dir=inkex_dir,
# 
)
