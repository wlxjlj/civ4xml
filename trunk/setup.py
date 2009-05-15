#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py

from distutils.core import setup
import py2exe

from civ4xml_constants import GC

main = 'civ4xml_GUI.pyw'
Mydata_files = [('.', ['Civ4XML_default_settings.ini', 'Civ4XML_settings.ini', 'gpl-3.0.txt', 'readme.txt', 'changelog.txt'])]

version_str = GC.VERSION_civ4xml

setup(
    name = 'civ4xmlview',
    version = version_str,
    description = 'Civ4 Xml View',
    script_name = 'setup.py',
    script_args = ['py2exe'],
    windows = [main],
    data_files = Mydata_files,
    options = {"py2exe": {
                            "includes": ["sip"],
                            "optimize": 1
                            }
                }
    )

def main():
    pass
    
if __name__=='__main__':
    main()
    raw_input('press enter')
