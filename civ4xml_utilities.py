#!/usr/bin/env python
# -*- coding: utf-8 -*-
# civ4xml_utilities.py

import sys
from PyQt4 import QtCore

from civ4xml_constants import GC

class DebugLog(object):
    def __init__(self):
        f = open('debug.txt', 'w')
        self.f = f
        sys.stdout = self
    
    def write(self, data):
        self.f.write(data)
        self.f.flush()
        sys.__stdout__.write(data)
    
    def close(self):
        sys.stdout = sys.__stdout__
    
    def __del__(self):
        self.f.write('===============================================================================')
        self.f.close()

class ErrorLog(object):
    def __init__(self):
        f = open('error.txt', 'w')
        self.f = f
        self.stderr = sys.stderr
        sys.stderr = self
    
    def write(self, data):
        self.f.write(data)
        self.f.flush()
        sys.__stderr__.write(data)
    
    def close(self):
        sys.stderr = sys.__stderr__
    
    def __del__(self):
        self.f.write('===============================================================================')
        self.f.close()

def readCiv4Registry():
    vanilla = QtCore.QSettings(QtCore.QSettings.NativeFormat, QtCore.QSettings.SystemScope, GC.REG_ORGANIZATION_Firaxis, GC.REG_APPLICATION_Vanilla)
    wl = QtCore.QSettings(QtCore.QSettings.NativeFormat, QtCore.QSettings.SystemScope, GC.REG_ORGANIZATION_Firaxis, GC.REG_APPLICATION_Wl)
    bts = QtCore.QSettings(QtCore.QSettings.NativeFormat, QtCore.QSettings.SystemScope, GC.REG_ORGANIZATION_Firaxis, GC.REG_APPLICATION_BtS)
    vanillaDir = vanilla.value(GC.REG_KEY_INSTALLDIR).toString()
    wlDir = wl.value(GC.REG_KEY_INSTALLDIR).toString()
    btsDir = bts.value(GC.REG_KEY_INSTALLDIR).toString()
    vanillaDir.replace('\\', '/')
    wlDir.replace('\\', '/')
    btsDir.replace('\\', '/')
    
    vanillaXmlDir = QtCore.QString()
    wlXmlDir = QtCore.QString()
    btsXmlDir = QtCore.QString()
    
    if not vanillaDir.isEmpty():
        vanillaXmlDir = vanillaDir + GC.Dir_Xml
    if not wlDir.isEmpty():
        wlXmlDir = wlDir + GC.Dir_Xml
    if not btsDir.isEmpty():
        btsXmlDir = btsDir + GC.Dir_Xml
        
    return (vanillaXmlDir, wlXmlDir, btsXmlDir)

def searchXml(filePath, bFirst = True):
    result = []
    fileInfo = QtCore.QFileInfo(filePath)
    fileName = fileInfo.fileName()
    
    ## current dir
    if fileInfo.isFile():
        result.append(fileInfo.absoluteFilePath())
        
        if bFirst and result:
            return result
    
    ## library
    
    ## Civ4 dir: bts, wl, vanilla
    if not GC.g_XmlDir_BtS.isEmpty():
        dirInfo = QtCore.QFileInfo(GC.g_XmlDir_BtS)
        temp = searchXmlDir(fileName, dirInfo, bFirst)
        
        if bFirst and temp:
            return temp
        elif temp:
            result.extend(temp)
    
    if not GC.g_XmlDir_Wl.isEmpty():
        dirInfo = QtCore.QFileInfo(GC.g_XmlDir_Wl)
        temp = searchXmlDir(fileName, dirInfo, bFirst)
        
        if bFirst and temp:
            return temp
        elif temp:
            result.extend(temp)
            
    if not GC.g_XmlDir_Vanilla.isEmpty():
        dirInfo = QtCore.QFileInfo(GC.g_XmlDir_Vanilla)
        temp = searchXmlDir(fileName, dirInfo, bFirst)
        
        if bFirst and temp:
            return temp
        elif temp:
            result.extend(temp)
    
    return result

def searchXmlDir(fileName, dirInfo, bFirst):
    result = []
    currentDir = QtCore.QDir(dirInfo.absoluteFilePath())
    infoList = currentDir.entryInfoList()
    
    for fileInfo in infoList:
        name = fileInfo.fileName()
        if fileInfo.isFile():
            if name == fileName:
                result.append(fileInfo.absoluteFilePath())
                if bFirst and result:
                    return result
        elif fileInfo.isDir() and name != '.' and name != '..':
            temp = searchXmlDir(fileName, fileInfo, bFirst)
            if bFirst and temp:
                return temp
            elif temp:
                result.extend(temp)
                    
    return result
    
def cmpTagValue(v1, v2):
    ## v1, v2 QString
    i, bi = v1.toInt()
    j, bj = v2.toInt()
    
    if bi and bj:
        return cmp(abs(i),abs(j))
    else:
        return cmp(v1, v2)
