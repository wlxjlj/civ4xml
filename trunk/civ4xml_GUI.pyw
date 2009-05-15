#!/usr/bin/env python
# -*- coding: utf-8 -*-
# civ4xml_GUI.py  -- main

import sys
from PyQt4 import QtCore, QtGui, QtXml ##, uic

from civ4xml_parser import *
from civ4xml_promoting_widget import *
import civ4xml_utilities as gu

#form_class, base_class = uic.loadUiType("civ4xml_window.ui")

class Civ4XmlWidget(Civ4XmlBaseWidget):
    def __init__(self, parent = None, filePath = None):
        Civ4XmlBaseWidget.__init__(self, parent)
        
        if self.openXml(filePath) == GC.XML_load_error :
            return
        
        self.connect(self.leaderTagTreeView, QtCore.SIGNAL("tagChanged(const QModelIndex&, const QModelIndex&)"), self.changeLeaderTag)
        self.connect(self.infoTreeView, QtCore.SIGNAL("tagChanged(const QModelIndex&, const QModelIndex&)"), self.changeTag)
        
        self.connect(self.civ4TagQueryModel, QtCore.SIGNAL("nodeTextChanged(const QModelIndex&)"), self.refreshAfterTagQueryEditing)
        self.connect(self.civ4DomModel, QtCore.SIGNAL("nodeTextChanged(const QModelIndex&)"), self.refreshAfterInfoEditing)

    def openXml(self, filePath):
        self.filePath = filePath
        
        self.domDocument = Civ4Xml(filePath)
        if self.domDocument.bXmlFail:
            self.bXmlFail = True
            return GC.XML_load_error 
        else:
            self.bXmlFail = False
        
        self.domDocumentModified = False
        self.root = self.domDocument.root        
        self.branchList, self.branchListFlag = self.domDocument.getBranchList()
        
        ## model
        self.civ4LeaderTagModel = self.updateCiv4LeaderTagModel(self)
        self.leaderTagList, self.leaderTagFlag = self.civ4LeaderTagModel.getLeaderTags()
        
        self.civ4DomModel = self.updateCiv4DomModel(0, self)
        self.civ4TagQueryModel = self.updateCiv4TagQueryModel(None, self)
        
        ## proxy model
        self.leaderTagProxyModel = QtGui.QSortFilterProxyModel(self)
        self.leaderTagProxyModel.setSourceModel(self.civ4LeaderTagModel)
        self.leaderTagTreeView.setModel(self.leaderTagProxyModel)
        
        #self.infoProxyModel = QtGui.QSortFilterProxyModel(self)
        self.infoProxyModel = Civ4InfoSortFilterProxyModel(self)
        self.infoProxyModel.setSourceModel(self.civ4DomModel)
        self.infoTreeView.setModel(self.infoProxyModel)
        
        self.tagQueryProxyModel = Civ4SortFilterProxyModel(self)
        self.tagQueryProxyModel.setSourceModel(self.civ4TagQueryModel)
        self.tagQueryTreeView.setModel(self.tagQueryProxyModel)
        
        ## delegate
        self.tagQueryItemDelegate = Civ4ItemDelegate(self)
        self.infoTreeView.setItemDelegateForColumn(GC.INFO_ColumnNumber_value, self.tagQueryItemDelegate)
        self.tagQueryTreeView.setItemDelegateForColumn(GC.TAGQUERY_ColumnNumber_value, self.tagQueryItemDelegate)
        
        ## filter
        self.leaderTagFilter.setProxyModel()
        self.infoFilter.setProxyModel()
        self.tagQueryFilter.setProxyModel()
        
        ## setting
        #self.leaderTagProxyModel.setDynamicSortFilter(True)
        #self.infoProxyModel.setDynamicSortFilter(True)
        
        self.leaderTagProxyModel.setFilterKeyColumn(-1)
        self.infoProxyModel.setFilterKeyColumn(-1)
        self.tagQueryProxyModel.setFilterKeyColumn(-1)
        
        self.leaderTagTreeView.setSortingEnabled(True)
        self.infoTreeView.setSortingEnabled(True)
        self.tagQueryTreeView.setSortingEnabled(True)
        
        self.leaderTagTreeView.sortByColumn(GC.LEADERTAG_ColumnNumber_index, QtCore.Qt.AscendingOrder)
        self.infoTreeView.sortByColumn(GC.INFO_ColumnNumber_index, QtCore.Qt.AscendingOrder)
        self.tagQueryTreeView.sortByColumn(GC.TAGQUERY_ColumnNumber_index, QtCore.Qt.AscendingOrder)
        
        self.processXmlInitialized()
        
    def loadXml(self, filePath):
        self.filePath = filePath
        
        domDocument = Civ4Xml(filePath)
        
        if domDocument.bXmlFail:
            return GC.XML_load_error
        else:
            self.domDocument = domDocument
            
        self.domDocumentModified = False
        self.root = self.domDocument.root
        self.branchList, self.branchListFlag = self.domDocument.getBranchList()
        
        self.updateCiv4LeaderTagModel()
        self.leaderTagList, self.leaderTagFlag = self.civ4LeaderTagModel.getLeaderTags()
        self.updateCiv4DomModel(0)
        self.updateCiv4TagQueryModel(None)
        
        self.processXmlInitialized()
    
    def processXmlInitialized(self):
        self.leaderTagFilter.updateColumnItem()
        self.infoFilter.updateColumnItem()
        self.tagQueryFilter.updateColumnItem()
        
        if GC.INI_display_expand_InfoTreeView:
            self.infoTreeView.expandAll()
        if GC.INI_display_expand_TagQueryTreeView:
            self.tagQueryTreeView.expandAll()
        
        self.displayXmlFileInfo()

    def updateCiv4LeaderTagModel(self, parent = None):
        if parent:
            return Civ4LeaderTagModel(self.branchList, self.branchListFlag)
        else:
            self.civ4LeaderTagModel.update(self.branchList, self.branchListFlag)
            self.civ4LeaderTagModel.reset()
            return self.civ4LeaderTagModel

    def updateCiv4DomModel(self, leaderTagIndex, parent = None):
        if parent:
            return Civ4DomModel(self.branchList[leaderTagIndex], parent)
        else:
            self.civ4DomModel.update(self.branchList[leaderTagIndex],  leaderTagIndex)
            self.civ4DomModel.reset()
            return self.civ4DomModel
        
    def updateCiv4TagQueryModel(self, currentItem = None, parent = None):
        leaderTagList = []
        tagList = []
        flag = u''
        templateItem = None
            
        if currentItem:
            templateItem, flag = currentItem.getQueryTagItem()
            name = templateItem.nodeName()
            generation = templateItem.getGeneration()
            if flag == GC.TAGQUERY_FLAG_TagPair:
                templateText = Civ4DomItem(templateItem.firstChildElement()).valueText()
        else:
            name = u''
            generation = 3  ## general depth in info xml file
        
        if GC.INI_display_stop_TagQueryModel or not name:
            nodeList = QtXml.QDomNodeList()
        else:
            nodeList = self.root.elementsByTagName(name)
        
        ## remove unqulified nodes
        if flag == GC.TAGQUERY_FLAG_TagPair:
            for i in range(nodeList.size()):
                node = nodeList.item(i)
                item = Civ4DomItem(node)
                
                if item.getGeneration() == generation:
                    text = Civ4DomItem(item.firstChildElement()).valueText()
                    if text == templateText:
                        leaderTag = item.getLeaderTag(self.branchListFlag)
                        leaderTagList.append(leaderTag)
                        tagList.append(node)
                        
        else:
            for i in range(nodeList.size()):
                node = nodeList.item(i)
                item = Civ4DomItem(node)
            
                if item.getGeneration() == generation:
                    leaderTag = item.getLeaderTag(self.branchListFlag)
                    leaderTagList.append(leaderTag)
                    tagList.append(node)
    
        leaderTags = (leaderTagList, self.leaderTagFlag)
        tags = (tagList, flag)
        
        if parent:
            return Civ4TagQueryModel(leaderTags, tags, parent)
        else:
            self.civ4TagQueryModel.update(leaderTags, tags,  templateItem)
            self.civ4TagQueryModel.reset()
            return self.civ4TagQueryModel

    def displayXmlFileInfo(self):
        self.infoTextList = QtCore.QStringList()
            
        self.infoTextList.append(self.filePath)
        if self.domDocument.schemaFileName:
            if self.domDocument.schema:
                self.infoTextList.append(self.domDocument.schema.filePath)
            else:
                self.infoTextList.append(self.domDocument.schemaFileName + u'not found')
        else:
            self.infoTextList.append(u'no schema file')
        self.infoTextBrowser.setPlainText(self.infoTextList.join(u'\n'))

    def displayTagQueryTemplateItemHierarchy(self):
        if self.civ4TagQueryModel.templateItem:
            hierarchyNameList = self.civ4TagQueryModel.templateItem.getHierarchyNameQStringList(self.root)
        else:
            hierarchyNameList = QtCore.QStringList()

        text = self.infoTextList.join(u'\n') + '\n\n' + hierarchyNameList.join(u'\n') + u'\n'
        self.infoTextBrowser.setPlainText(text)
    
    def isXmlModified(self):
        return self.domDocumentModified
    
    def setXmlModified(self, bModified):
        self.domDocumentModified = bModified
        
        if bModified:
            self.emit(QtCore.SIGNAL("xmlModified(bool)"),  bModified)
        
    ## SLOTs
    def changeLeaderTag(self, currentIndex,  previousIndex):
        self.updateCiv4DomModel(self.leaderTagProxyModel.mapToSource(currentIndex).row())
        
        ## redundant, model.reset() => proxymodel.reset() => view.reset()
        #self.infoTreeView.reset()  
        
        if GC.INI_display_expand_InfoTreeView:
            self.infoTreeView.expandAll()

    def changeTag(self, currentIndex,  previousIndex):
        if currentIndex.isValid():
            currentItem = self.infoProxyModel.mapToSource(currentIndex).internalPointer()
            self.updateCiv4TagQueryModel(currentItem)
            
            self.displayTagQueryTemplateItemHierarchy()
            
            if GC.INI_display_stop_TagQueryModel:
                return
            
            if GC.INI_display_expand_TagQueryTreeView:
                self.tagQueryTreeView.expandAll()
    
    def refreshAfterInfoEditing(self,  editedItemIndex):
        self.setXmlModified(True)
        
        item = editedItemIndex.internalPointer()
        leaderTagIndexNumber = self.civ4DomModel.leaderTagIndex
        leaderTagNode = self.leaderTagList[leaderTagIndexNumber]
        
        ## inform LeaderTagTreeView dataChanged
        if leaderTagNode == item.node():
            index = self.civ4LeaderTagModel.getLeaderTagIndex(leaderTagIndexNumber, GC.LEADERTAG_ColumnNumber_value)
            self.civ4LeaderTagModel.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
        
        ## ## inform TagQueryTreeView dataChanged
        self.tagQueryTreeView.viewport().update()
        
    def refreshAfterTagQueryEditing(self, editedItemIndex):
        self.setXmlModified(True)
        
        leaderTagIndex = self.civ4TagQueryModel.getLeaderTagIndex(editedItemIndex)
        item = editedItemIndex.internalPointer()
        leaderTagItem = leaderTagIndex.internalPointer()
        
        leaderTagNodeByTagQueryItem = leaderTagItem.node()
        leaderTagNodeByInfoTreeView = self.leaderTagList[self.civ4DomModel.leaderTagIndex]
        
        ## inform InfoTreeView dataChanged
        if leaderTagNodeByTagQueryItem == leaderTagNodeByInfoTreeView:
            index = self.civ4DomModel.getIndexByItem(item)
            
            if index:
                if self.civ4TagQueryModel.tagFlag == GC.TAGQUERY_FLAG_TagPair:
                    ## need to improve if there exists a comment-node child
                    index = index.child(1, GC.INFO_ColumnNumber_value)
                else:
                    index = index.sibling(index.row(), GC.INFO_ColumnNumber_value)
                    
                self.civ4DomModel.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
                
        ## inform LeaderTagTreeView dataChanged
        if leaderTagNodeByTagQueryItem == item.node():
            columnNumber = GC.LEADERTAG_ColumnNumber_value
            for i, node in enumerate(self.leaderTagList):
                if node == leaderTagNodeByTagQueryItem:
                    index = self.civ4LeaderTagModel.getLeaderTagIndex(i, columnNumber)
                    self.civ4LeaderTagModel.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
                    break


class Civ4Window(QtGui.QMainWindow):
    def __init__(self, parent = None, flag = 0, *args):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.setupUi()
        self.createMenu()
        
        self.connect(self.tabBar, QtCore.SIGNAL("doubleClicked(const int&)"), self.closeFile)
        
        self.init()

    def setupUi(self):
        self.resize(800, 600)
        
        self.centralwidget = QtGui.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        
        ## tabwidget
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.verticalLayout.addWidget(self.tabWidget)
        
        self.tab = QtGui.QWidget(self)
        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.setCurrentIndex(0)
        
        ## menubar
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 24))
        
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuSettings = QtGui.QMenu(self.menubar)
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        ## statusbar
        self.statusbar = QtGui.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        
        ## tabbar, not in ui
        self.tabBar = Civ4TabBar(self.tabWidget)
        self.tabWidget.setTabBar(self.tabBar)
    
        self.retranslateUi()
        #QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("Civ4Window", "Civ4 XML View", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("Civ4Window", "new", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(QtGui.QApplication.translate("Civ4Window", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.menuView.setTitle(QtGui.QApplication.translate("Civ4Window", "&View", None, QtGui.QApplication.UnicodeUTF8))
        self.menuSettings.setTitle(QtGui.QApplication.translate("Civ4Window", "&Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelp.setTitle(QtGui.QApplication.translate("Civ4Window", "&Help", None, QtGui.QApplication.UnicodeUTF8))

    def createMenu(self):
        ## File
        self.menuFile.addAction(self.tr("&Open..."), self.openFile, QtGui.QKeySequence.Open)
        self.menuFile.addAction(self.tr("&Load..."), self.loadFile, QtGui.QKeySequence(self.tr("Ctrl+L")))
        self.menuOpenRecentFiles = self.menuFile.addMenu(self.tr("Open Recent Files"))
        
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.tr("&Close"), self.closeFile, QtGui.QKeySequence(self.tr("Ctrl+W")))
        self.menuFile.addSeparator()
        self.actionSaveAs = self.menuFile.addAction(self.tr("Save as..."), self.saveAs, QtGui.QKeySequence.Save)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.tr("E&xit"), self, QtCore.SLOT("close()"), QtGui.QKeySequence(self.tr("Ctrl+Q")))
        
        #### Recent Files
        self.actionListOpenRecentFiles = []
        for i in range(GC.INI_recent_files_size):
            action = self.menuOpenRecentFiles.addAction(unicode(i+1),  self.openRecentFiles)
            action.setVisible(False)
            self.actionListOpenRecentFiles.append(action)
        self.menuOpenRecentFiles.addSeparator()
        self.menuOpenRecentFiles.addAction(self.tr("Clear"), self.clearRecentFiles)
        self.menuOpenRecentFiles.setEnabled(False)
        
        ## View
        self.menuView.addAction(self.tr("Expand Info TreeView"), self.expandInfoTreeView, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_expand_InfoTreeView)))
        self.menuView.addAction(self.tr("Collapse Info TreeView"), self.collapseInfoTreeView, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_collapse_InfoTreeView)))
        self.menuView.addAction(self.tr("Expand Tag Auto Query TreeView"), self.expandTagQueryTreeView, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_expand_TagQueryTreeView)))
        self.menuView.addAction(self.tr("Collapse Tag Auto Query TreeView"), self.collapseTagQueryTreeView, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_collapse_TagQueryTreeView)))
        self.menuView.addSeparator()
        self.actionLeaderTagFilter = self.menuView.addAction(self.tr("LeaderTag Filter"), self.switchLeaderTagFilter, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_switch_LeaderTagFilter)))
        self.actionInfoFilter = self.menuView.addAction(self.tr("Info Filter"), self.switchInfoFilter, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_switch_InfoFilter)))
        self.actionTagQueryFilter = self.menuView.addAction(self.tr("Tag Query Filter"), self.switchTagQueryFilter, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_switch_TagQueryFilter)))
        self.menuView.addSeparator()
        self.actionSwtichTagQuery = self.menuView.addAction(self.tr("Stop Tag Query"), self.swtichTagQuery)
        self.menuView.addSeparator()
        self.menuView.addAction(self.tr("View Source"), self.displayXmlSource, QtGui.QKeySequence(self.tr(GC.INI_shortcutKey_view_XmlSource)))
        
        
        self.actionSwtichTagQuery.setCheckable(True)
        self.actionSwtichTagQuery.setStatusTip(self.tr("Start/Stop Tag Query"))
        
        ## Settings
        self.menuSettings.addAction(self.tr("Save Display Settings"), self.saveSettings)
        self.menuSettings.addSeparator()
        self.actionUserSetting = self.menuSettings.addAction(self.tr("User's Display Settings"), self.switchSettings)
        self.actionNoSetting = self.menuSettings.addAction(self.tr("Defaut Display Settings"), self.switchSettings)
        
        self.actionUserSetting.setCheckable(True)
        self.actionNoSetting.setCheckable(True)
        
        self.actionGroupSetting = QtGui.QActionGroup(self.menuSettings) 
        self.actionGroupSetting.addAction(self.actionUserSetting)
        self.actionGroupSetting.addAction(self.actionNoSetting)
        self.actionUserSetting.setChecked(True)
        
        ## Help
        #self.menuHelp.addAction(self.tr("&Test..."), self.test, QtGui.QKeySequence(self.tr("Ctrl+Z")))
        
        self.menuHelp.addAction(self.tr("&Help Contents"), self.showHelp, QtGui.QKeySequence.HelpContents) 
        self.menuHelp.addAction(self.tr("&License"), self.showLicense) 
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.tr("About &Civ4 XML View"), self.showAbout) 
        self.menuHelp.addAction(self.tr("About &Qt"), QtGui.qApp, QtCore.SLOT("aboutQt()")) 

    def init(self):
        self.oldTabCount = 0
        self.iCurrentSourceViewWidgetID = 0
        self.bActiveWindowHelpContents = False
        self.dictXmlSourceViewWidget = {}  ## int-QWidget(Civ4XmlSourceViewWidget) dict
        
        self.processInitSettings()
        
        for arg in sys.argv[1:]:
            fileInfo = QtCore.QFileInfo(arg)
            if fileInfo.isFile():
                self.openFile(arg)

    def currentIdx(self):
        if not self.oldTabCount:
            return -1
        else:
            return self.tabWidget.currentIndex()
    
    def currentTab(self):
        return self.tabWidget.currentWidget()
    
    def hasNonEmptyTagPage(self):
        return bool(self.oldTabCount)
        
    def strippedName(self, filePath):
        return QtCore.QFileInfo(filePath).fileName()
        
    def currentCustomWidgets(self):
        if not self.oldTabCount:
            return None
            
        currentTab = self.currentTab()
        splitter = currentTab.splitter
        splitterL = currentTab.splitterL
        splitterR = currentTab.splitterR
        headerLeaderTag = currentTab.leaderTagTreeView.header()
        headerInfo = currentTab.infoTreeView.header()
        headerTagQuery = currentTab.tagQueryTreeView.header()
        
        return (splitter, splitterL, splitterR, headerLeaderTag, headerInfo, headerTagQuery)
    
    def processInitSettings(self):
        ok = True
        
        ## startup path
        self.xmlPath = GC.g_DICT_settings[GC.INI_path_startup_key]
        
        ## recent files
        c = 0
        for i in range(GC.INI_recent_files_size):
            filePath = GC.g_DICT_settings[GC.INI_recent_files_key][i]
            fileInfo = QtCore.QFileInfo(filePath)
            if fileInfo.isFile():
                action = self.actionListOpenRecentFiles[c]
                action.setData(QtCore.QVariant(filePath))
                action.setText(self.tr('%1. %2').arg(c + 1).arg(filePath))
                action.setVisible(True)
                c += 1
        
        if c:
            self.menuOpenRecentFiles.setEnabled(True)
            
        ## mainWindow
        ok = self.restoreGeometry(GC.g_DICT_settings[GC.INI_display_mainWindow])
        
        return ok
    
    def processTabPageSettings(self, bDefault = False):
        ok = True
        
        if bDefault:
            settings = GC.g_DICT_default_settings
        else:
            settings = GC.g_DICT_settings
        
        ## splitter, header
        if self.oldTabCount:
            widgetTuple = self.currentCustomWidgets()
        
            if widgetTuple:
                for i, name in enumerate(GC.INI_display_TUPLE_CustomWidgetName):
                    ok = widgetTuple[i].restoreState(settings[name]) and ok
    
        ## filter
        if GC.INI_display_hide_LeaderTagFilter:
            self.currentTab().leaderTagFilter.hide()
        if GC.INI_display_hide_InfoFilter:
            self.currentTab().infoFilter.hide()
        if GC.INI_display_hide_TagQueryFilter:
            self.currentTab().tagQueryFilter.hide()
        
        return ok

    def setupTabSignals(self, newTab):
        self.connect(newTab, QtCore.SIGNAL("xmlModified(bool)"), self.remindXmlModified)
        self.connect(newTab.leaderTagTreeView, QtCore.SIGNAL("viewNodeSource(const QModelIndex&)"), self.displayXmlNodeSource)
        self.connect(newTab.infoTreeView, QtCore.SIGNAL("viewNodeSource(const QModelIndex&)"), self.displayXmlNodeSource)
        self.connect(newTab.tagQueryTreeView, QtCore.SIGNAL("viewNodeSource(const QModelIndex&)"), self.displayXmlNodeSource)
        
        newTab.tagQueryTreeView.getContextMenu().addAction(self.tr("View Table Text"), self.displayTableText)
        newTab.tagQueryTreeView.getContextMenu().addAction(self.tr("View Statistics Text"), self.displayStatsTableText)
    
    def initXmlSourceViewWidget(self, iId = 0):
        if not iId:
            self.iCurrentSourceViewWidgetID += 1
            iId = self.iCurrentSourceViewWidgetID
            
        widget = Civ4XmlSourceViewWidget(None, iId)
            
        self.dictXmlSourceViewWidget[iId] = widget
        self.connect(widget, QtCore.SIGNAL("sourceViewWidgetClosing(int)"), self.updateDictXmlSourceViewWidget)
        
        if self.oldTabCount:
            widget.filePath = self.currentTab().filePath
        else:
            widget.filePath = GC.g_appDirName
        
        return widget

    def addRecentFile(self,  filePath):
        index = self.locateRecentFile(filePath)
        
        if index >= 0:
            self.removeRecentFile(index)
            
        for i in range(GC.INI_recent_files_size - 1,  0,  -1):
            new= self.actionListOpenRecentFiles[i-1]
            old = self.actionListOpenRecentFiles[i]            
            
            if new.isVisible():
                old.setData(new.data())                
                old.setText(self.tr('%1. %2').arg(i + 1).arg(new.data().toString()))
                old.setVisible(True)
        
        action = self.actionListOpenRecentFiles[0]
        action.setData(QtCore.QVariant(filePath))
        action.setText(self.tr('%1. %2').arg(1).arg(filePath))
        action.setVisible(True)
        self.menuOpenRecentFiles.setEnabled(True)
        
        self.saveRecentFilesSettings()
            
    def removeRecentFile(self,  index):
        for i in range(index, GC.INI_recent_files_size - 1):
            ## new - upper; old -lower
            new= self.actionListOpenRecentFiles[i]
            old = self.actionListOpenRecentFiles[i+1]
            
            if old.isVisible():
                new.setData(old.data())
                new.setText(self.tr('%1. %2').arg(i + 1).arg(old.data().toString()))
            else:
                new.setVisible(False)
                break
                
        if index == 0 and not self.actionListOpenRecentFiles[0].isVisible():
            self.menuOpenRecentFiles.setEnabled(False)
        
        self.saveRecentFilesSettings()
            
    def locateRecentFile(self, filePath): 
        for i in range(GC.INI_recent_files_size):
            action = self.actionListOpenRecentFiles[i]
            if action.data().toString() == filePath:
                return i
        
        return -1
    
    def checkRecentFiles(self, bCheckName = False):
        pass
    
    def saveRecentFilesSettings(self):
        GC.g_settings.beginGroup(GC.INI_GROUP_RecentFiles)
        
        for i in range(GC.INI_recent_files_size):
            action = self.actionListOpenRecentFiles[i]
            if action.isVisible():
                GC.g_settings.setValue(unicode(i), action.data())
            else:
                GC.g_settings.setValue(unicode(i), QtCore.QVariant())
        
        GC.g_settings.endGroup()
        
    def informXmlFileError(self, filePath = u'the file'):
        QtGui.QMessageBox.warning(self, self.tr("Xml File Error"), self.tr("This program was unable to read %1.").arg(self.strippedName(filePath)), QtGui.QMessageBox.Ok ) 
        
    def test(self):
        print 'test'
        print 'test end'

    ## virtual protected
    def closeEvent(self, event):
        ## check saved/unsaved
        if self.oldTabCount:
            bUnsaved = False
            
            for i in range(self.tabWidget.count()):
                if self.tabWidget.widget(i).isXmlModified():
                    bUnsaved = True
                    break
            
            if bUnsaved:
                if QtGui.QMessageBox.warning(self, self.tr("Exit"),
                        self.tr("There are xml files modified but not saved. Do you really want to exit?"),
                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No ) == QtGui.QMessageBox.No:
                    event.ignore()
                    return
        
        ## close all Civ4XmlSourceViewWidget
        for widget in self.dictXmlSourceViewWidget.values():
            self.disconnect(widget, QtCore.SIGNAL("sourceViewWidgetClosing(int)"), self.updateDictXmlSourceViewWidget)
            widget.close()
        
        self.dictXmlSourceViewWidget.clear()

        QtGui.QMainWindow.closeEvent(self, event)
            
    ## SLOTs
    def openFile(self,  filePath = None):
        if not filePath:
            if self.oldTabCount:
                dir = self.currentTab().filePath
            else:
                dir = self.xmlPath

            filePath = QtGui.QFileDialog.getOpenFileName(self, QtCore.QString(), dir, self.tr("XML files (*.xml);;All files (*.*)"))

        if filePath:
            newTab = Civ4XmlWidget(self, filePath)
            
            if newTab.bXmlFail:
                newTab.close()
                self.informXmlFileError(filePath)
                return GC.XML_load_error
            
            if not self.oldTabCount:
                self.tabWidget.removeTab(0)
                self.tab.close()
        
            self.oldTabCount += 1
            
            self.setupTabSignals(newTab)
            
            newTabIdx = self.tabWidget.insertTab(self.oldTabCount, newTab, self.strippedName(filePath))
            self.tabWidget.setCurrentIndex(newTabIdx)
            newTab.show()
            
            self.processTabPageSettings(not self.actionUserSetting.isChecked())
            self.addRecentFile(filePath)
            self.xmlPath = filePath
            
    def loadFile(self, filePath = None):
        if self.oldTabCount: 
            currentTab = self.currentTab()
            if currentTab.isXmlModified():
                button = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("%1 has been modified. Do you really want to load another file?").arg(self.strippedName(currentTab.filePath)),
                            QtGui.QMessageBox.Save, QtGui.QMessageBox.Discard, QtGui.QMessageBox.Abort )

                if button == QtGui.QMessageBox.Abort:
                    return
                elif button == QtGui.QMessageBox.Save:
                    result = self.saveAs(True)
                    if result != 1:
                        return

        if not filePath:
            if self.oldTabCount:
                dir = self.currentTab().filePath
            else:
                dir = self.xmlPath

            filePath = QtGui.QFileDialog.getOpenFileName(self, self.tr("Load"), dir, self.tr("XML files (*.xml);;All files (*.*)"))

        if filePath:
            if not self.oldTabCount:
                newTab = Civ4XmlWidget(self, filePath)
                
                if newTab.bXmlFail:
                    newTab.close()
                    self.informXmlFileError(filePath)
                    return GC.XML_load_error
                
                self.tabWidget.removeTab(0)
                self.tab.close()
                
                newTabIdx = self.tabWidget.insertTab(self.oldTabCount, newTab, self.strippedName(filePath))
                newTab.show()
                self.tabWidget.setCurrentIndex(newTabIdx)
            
            else:
                currentTab = self.currentTab()
                if currentTab.loadXml(filePath) == GC.XML_load_error:
                    return GC.XML_load_error
                    
                currentTabIdx = self.tabWidget.currentIndex()
                self.tabWidget.setTabText(currentTabIdx, filePath)
            
            self.addRecentFile(filePath)
            self.xmlPath = filePath
            
    def closeFile(self, index = -1):
        if self.oldTabCount:            
            if index == -1:
                currentIdx = self.tabWidget.currentIndex()
            else:
                currentIdx = index
            currentTab = self.tabWidget.widget(currentIdx)
            
            if currentTab.isXmlModified():
                button = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("%1 has been modified. Do you really want to close?").arg(self.strippedName(currentTab.filePath)),
                            QtGui.QMessageBox.Save, QtGui.QMessageBox.Discard, QtGui.QMessageBox.Abort )
                    
                if button == QtGui.QMessageBox.Abort:
                    return
                elif button == QtGui.QMessageBox.Save:
                    result = self.saveAs(True)
                    if result != GC.SaveAs_close:
                        return
            
            self.tabWidget.removeTab(currentIdx)
            self.oldTabCount -= 1
            currentTab.close()
            
            if not self.oldTabCount:
                self.tabWidget.insertTab(self.oldTabCount, self.tab, self.tr(u'new'))
                self.tab.show()
    
    def openRecentFiles(self):
        action = self.sender()
        
        filePath = action.data().toString()
        index,  _ = action.text().split(u'. ')[0].toInt()
        
        fileInfo = QtCore.QFileInfo(filePath)
        
        if fileInfo.isFile():
            self.openFile(filePath)
        else:
            self.removeRecentFile(index - 1)
    
    def saveAs(self, bClose = False):
        if self.oldTabCount:
            tab = self.currentTab()
            document = tab.domDocument
            
            filePath = QtGui.QFileDialog.getSaveFileName(self, QtCore.QString(), tab.filePath, self.tr("XML files (*.xml);;All files (*.*)"))
            
            if not filePath.isEmpty():
                saveFile = QtCore.QFile(filePath)
                
                if not saveFile.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                    QtGui.QMessageBox.warning(self, self.tr("Codecs"), self.tr("Cannot write file %1:\n%2").arg(filePath).arg(saveFile.errorString()))
                    return
                
                out = QtCore.QTextStream(saveFile)
                document.save(out, 4)
                out.flush()
                saveFile.close()
                
                self.addRecentFile(filePath)
                
                if bClose:
                    return GC.SaveAs_close
                
                self.tabWidget.setTabText(self.currentIdx(), self.strippedName(filePath))
                tab.filePath = filePath
                tab.displayXmlFileInfo()
                tab.domDocumentModified = False
     
    def remindXmlModified(self, bModified):
        if bModified:
            widget = self.sender()
            
            for i in range(self.tabWidget.count()):
                if self.tabWidget.widget(i) == widget:
                    title = self.strippedName(widget.filePath) + u' *'
                    self.tabWidget.setTabText(i, title)
                    return
    
    def clearRecentFiles(self):
        for i in range(GC.INI_recent_files_size):
            self.actionListOpenRecentFiles[i].setVisible(False)
        
        self.menuOpenRecentFiles.setEnabled(False)
        
    def expandInfoTreeView(self):
        if self.oldTabCount:
            currentTabIdx = self.tabWidget.currentIndex()
            currentTab = self.tabWidget.widget(currentTabIdx)
            currentTab.infoTreeView.expandAll()
        
    def collapseInfoTreeView(self):
        if self.oldTabCount:
            currentTabIdx = self.tabWidget.currentIndex()
            currentTab = self.tabWidget.widget(currentTabIdx)
            currentTab.infoTreeView.collapseAll()
            
    def expandTagQueryTreeView(self):
        if self.oldTabCount:
            currentTabIdx = self.tabWidget.currentIndex()
            currentTab = self.tabWidget.widget(currentTabIdx)
            currentTab.tagQueryTreeView.expandAll()
        
    def collapseTagQueryTreeView(self):
        if self.oldTabCount:
            currentTabIdx = self.tabWidget.currentIndex()
            currentTab = self.tabWidget.widget(currentTabIdx)
            currentTab.tagQueryTreeView.collapseAll()            
    
    def switchLeaderTagFilter(self):        
        if self.oldTabCount:
            filter = self.currentTab().leaderTagFilter
            if filter.isHidden():
                filter.show()
            else:
                filter.hide()
            
    def switchInfoFilter(self):
        if self.oldTabCount:
            filter = self.currentTab().infoFilter
            if filter.isHidden():
                filter.show()
            else:
                filter.hide()
    
    def switchTagQueryFilter(self):
        if self.oldTabCount:
            filter = self.currentTab().tagQueryFilter
            if filter.isHidden():
                filter.show()
            else:
                filter.hide()
    
    def swtichTagQuery(self):
        GC.INI_display_stop_TagQueryModel = self.actionSwtichTagQuery.isChecked()
    
    def displayXmlNodeSource(self, index = None):
        tab = self.currentTab()
        
        if index:
            if self.sender() == tab.leaderTagTreeView:
                item = tab.branchList[index.row()]
            else:
                item = index.internalPointer()
        else:            
            item = tab.domDocument
        
        if self.oldTabCount:
            widget = self.initXmlSourceViewWidget()
            widget.filePath = tab.filePath
            
            widget.setNode(item)
            widget.show()

    def displayXmlSource(self):
        self.displayXmlNodeSource()
    
    def updateDictXmlSourceViewWidget(self, iId):
        '''remove iId-widget from self.dictXmlSourceViewWidget to avoid closing widget twice'''
        assert iId in self.dictXmlSourceViewWidget
        
        GC.g_temp_widget = self.dictXmlSourceViewWidget.pop(iId)
    
    def displayTableText(self):
        tab = self.currentTab()
        text = tab.tagQueryTreeView.model().toHtml()
        
        if self.oldTabCount:
            widget = self.initXmlSourceViewWidget()
            widget.filePath = tab.filePath
            
            widget.setPlainTextToTextEdit(text)
            widget.show()

    def displayStatsTableText(self):
        tab = self.currentTab()
        text = tab.tagQueryTreeView.model().toHtmlStats()
        
        if self.oldTabCount:
            widget = self.initXmlSourceViewWidget()
            widget.filePath = tab.filePath
            
            widget.setPlainTextToTextEdit(text)
            widget.show()

    def saveSettings(self):
        tab = self.currentTab()
        
        ## filter
        GC.g_settings.beginGroup(GC.INI_GROUP_Filter)
        
        GC.g_settings.setValue(GC.INI_filter_deep_key, QtCore.QVariant(GC.INI_filter_deep))
        
        GC.g_settings.endGroup()
        
        ## display
        GC.g_settings.beginGroup(GC.INI_GROUP_display)
        
        #### mainWindow
        GC.g_settings.setValue(GC.INI_display_mainWindow, QtCore.QVariant(self.saveGeometry()))
        
        if self.oldTabCount:
            ## splitter, header
            widgetTuple = self.currentCustomWidgets()
        
            for i, name in enumerate(GC.INI_display_TUPLE_CustomWidgetName):
                GC.g_settings.setValue(name, QtCore.QVariant(widgetTuple[i].saveState()))
                
                ## update setting-cache GC.g_DICT_settings
                GC.g_DICT_settings[name] = GC.g_settings.value(name).toByteArray()
        
            #### filter
            h1 = tab.leaderTagFilter.isHidden()
            h2 = tab.infoFilter.isHidden()
            h3 = tab.tagQueryFilter.isHidden()
            
            GC.g_settings.setValue(GC.INI_display_hide_LeaderTagFilter_key, QtCore.QVariant(h1))
            GC.g_settings.setValue(GC.INI_display_hide_InfoFilter_key, QtCore.QVariant(h2))
            GC.g_settings.setValue(GC.INI_display_hide_TagQueryFilter_key, QtCore.QVariant(h3))
            GC.INI_display_hide_LeaderTagFilter = h1
            GC.INI_display_hide_InfoFilter = h2
            GC.INI_display_hide_TagQueryFilter = h3
            
            #### expand/collapse
            GC.g_settings.setValue(GC.INI_display_expand_InfoTreeView_key, QtCore.QVariant(GC.INI_display_expand_InfoTreeView))
            GC.g_settings.setValue(GC.INI_display_expand_TagQueryTreeView_key, QtCore.QVariant(GC.INI_display_expand_TagQueryTreeView))

        GC.g_settings.endGroup()
        
    def switchSettings(self):
        if self.actionUserSetting.isChecked():
            self.processTabPageSettings()
        else:
            self.processTabPageSettings(True)

    def showHelp(self):
        if GC.WINDOW_help_contents in self.dictXmlSourceViewWidget:
            widget = self.dictXmlSourceViewWidget[GC.WINDOW_help_contents]
            widget.setWindowState(widget.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            widget.raise_()
            
        else:
            readmeFileInfo = QtCore.QFileInfo(GC.g_appDir, GC.HELP_FileName)
            f = QtCore.QFile(readmeFileInfo.absoluteFilePath())
        
            if f.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(f) 
                text = stream.readAll()
                f.close()
                
            else:
                text = self.tr(u'readme.txt not found')
        
            widget = self.initXmlSourceViewWidget(GC.WINDOW_help_contents)
            widget.setHelpContents(text)
            widget.show()

    def showAbout(self):
        m = Civ4XmlMessageBox()
        m.setup(m.getAbout)
        m.exec_()
        
    def showLicense(self):
        m = Civ4XmlMessageBox()
        m.setup(m.getLicense)
        m.exec_()


def initGlobals(app, argv):
    GC.g_XmlDir_Vanilla, GC.g_XmlDir_Wl, GC.g_XmlDir_BtS = gu.readCiv4Registry()
    
    GC.g_appInfo = QtCore.QFileInfo(argv[0])
    GC.g_appDir = GC.g_appInfo.absoluteDir()
    GC.g_appDirName = GC.g_appInfo.absolutePath()
    GC.g_appName = GC.g_appInfo.fileName()
    
    QtCore.QSettings.setUserIniPath(GC.g_appDirName)
    GC.g_iniFileInfo = QtCore.QFileInfo(GC.g_appDir, GC.INI_FileName)
    
    initSettings()

def initSettings():
    GC.g_settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, GC.INI_FileBaseName)
    GC.g_default_settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, GC.INI_DEFAULT_FileBaseName)
    GC.g_DICT_settings = {}  ## unicode-QByteArray dict
    GC.g_DICT_default_settings = {}  ## unicode-QByteArray dict
    
    ## global
    loadGlobalSettings()
    
    ## display
    if GC.g_iniFileInfo.isFile():
        loadDisplaySettings(GC.g_DICT_settings, GC.g_settings)
    else:
        loadDisplaySettings(GC.g_DICT_settings, GC.g_default_settings)
    
    loadDisplaySettings(GC.g_DICT_default_settings, GC.g_default_settings)

def loadGlobalSettings(): 
    ## path
    GC.g_settings.beginGroup(GC.INI_GROUP_Path)
    
    dirName = GC.g_settings.value(GC.INI_path_startup_key).toString()
    if dirName:
        GC.g_DICT_settings[GC.INI_path_startup_key] = dirName
    else:
        GC.g_DICT_settings[GC.INI_path_startup_key] = GC.g_appDirName
        
    GC.g_settings.endGroup()
    
    ## filter
    GC.g_settings.beginGroup(GC.INI_GROUP_Filter)
    
    GC.INI_filter_deep = GC.g_settings.value(GC.INI_filter_deep_key).toBool()
    
    GC.g_settings.endGroup()
    
    ## recent files
    GC.g_settings.beginGroup(GC.INI_GROUP_RecentFiles)
    
    size,  ok = GC.g_settings.value(GC.INI_recent_files_sizename).toInt()
    
    if ok:
        if size > 0 and size < 100:
            GC.INI_recent_files_size = size
    
    GC.g_DICT_settings[GC.INI_recent_files_key] = []
    for i in range(GC.INI_recent_files_size):
        GC.g_DICT_settings[GC.INI_recent_files_key].append(GC.g_settings.value(unicode(i)).toString())
    
    GC.g_settings.endGroup()
    
    ## display
    GC.g_settings.beginGroup(GC.INI_GROUP_display)

    #### filter
    GC.INI_display_hide_LeaderTagFilter = GC.g_settings.value(GC.INI_display_hide_LeaderTagFilter_key).toBool()
    GC.INI_display_hide_InfoFilter = GC.g_settings.value(GC.INI_display_hide_InfoFilter_key).toBool()
    GC.INI_display_hide_TagQueryFilter = GC.g_settings.value(GC.INI_display_hide_TagQueryFilter_key).toBool()
    
    #### expand/collapse
    GC.INI_display_expand_InfoTreeView = GC.g_settings.value(GC.INI_display_expand_InfoTreeView_key).toBool()
    GC.INI_display_expand_TagQueryTreeView = GC.g_settings.value(GC.INI_display_expand_TagQueryTreeView_key).toBool()

    GC.g_settings.endGroup()

def loadDisplaySettings(g_DICT, settings): 
    ## display
    settings.beginGroup(GC.INI_GROUP_display)
    
    #### mainWindow
    g_DICT[GC.INI_display_mainWindow] = settings.value(GC.INI_display_mainWindow).toByteArray()
    
    #### splitter, header
    for name in GC.INI_display_TUPLE_CustomWidgetName:
        g_DICT[name] = settings.value(name).toByteArray()
    
    settings.endGroup()
    
    
def main():
    if GC.VERSION_debug:
        g_D = gu.DebugLog()
        g_E = gu.ErrorLog()
    
    app = QtGui.QApplication(sys.argv)
    
    initGlobals(app, sys.argv)
    
    mywindow = Civ4Window()
    mywindow.show()
    app.exec_()
    
    if GC.VERSION_debug:
        g_D.close()
        g_E.close()

if __name__=='__main__':
    main()
