#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py

from distutils.core import setup
import py2exe

main = 'civ4xml_GUI.pyw'

Mydata_files = [('.', ['Civ4XML_default_settings.ini', 'Civ4XML_settings.ini', 'gpl-3.0.txt', 'readme.txt', 'changelog.txt'])]

setup(
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
