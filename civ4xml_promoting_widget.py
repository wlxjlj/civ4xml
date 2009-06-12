#!/usr/bin/env python
# -*- coding: utf-8 -*-
# civ4xml_promoting_widget.py

import sys
from PyQt4 import QtCore, QtGui

from civ4xml_constants import GC
from civ4xml_parser import *

class Civ4LineEdit(QtGui.QLineEdit):
    def __init__(self,  parent = None):
        QtGui.QLineEdit.__init__(self,  parent)
    
    def setValue(self, text):
        QtGui.QLineEdit.setText(self, unicode(text))
    
    def value(self):
        return QtGui.QLineEdit.text(self)
    
class Civ4ItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self,  parent = None):
        QtGui.QStyledItemDelegate.__init__(self,  parent)
    
    def createEditor(self, parent, option, index): 
        data = index.data()
        editor = QtGui.QLineEdit(parent)
        self.connect(editor, QtCore.SIGNAL("editingFinished()"), self.commitAndCloseEditor) 
        return editor

    def setEditorData(self, editor, index): 
        editor.setText(index.data().toString())

    def setModelData(self, editor, model, index): 
        sourceModel = model.sourceModel()
        sourceIndex = model.mapToSource(index)
        sourceModel.setData(sourceIndex,  QtCore.QVariant(editor.text()))
        
    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(QtCore.SIGNAL("commitData(QWidget *)"), editor)
        self.emit(QtCore.SIGNAL("closeEditor(QWidget *)"), editor) 

class Civ4NoProxyItemDelegate(Civ4ItemDelegate):
    def __init__(self,  parent = None):
        Civ4ItemDelegate.__init__(self,  parent)
    
    def setModelData(self, editor, model, index): 
        model.setData(index,  QtCore.QVariant(editor.text()))
    
class Civ4TreeView(QtGui.QTreeView):
    def __init__(self, parent = None):
        QtGui.QTreeView.__init__(self, parent)
        
        self.contextMenu = QtGui.QMenu(self)
        self.actionViewNodeSource = self.contextMenu.addAction(self.tr("View Node Source"), self.sendViewNodeSourceSignal)
    
    def getContextMenu(self):
        return self.contextMenu
    
    ## virtual protected
    def contextMenuEvent(self, event):
        #index = self.indexAt(event.pos())
        #self.setCurrentIndex(index)
        
        self.contextMenu.exec_(event.globalPos()) 

    ## SLOT
    def currentChanged(self, current, previous):
        QtGui.QTreeView.currentChanged(self, current, previous)
        
        if current != previous:
            if current.row() != previous.row():
                self.emit(QtCore.SIGNAL("tagChanged(const QModelIndex&, const QModelIndex&)"), current,  previous)
            else:
                if current.parent() != previous.parent():
                    self.emit(QtCore.SIGNAL("tagChanged(const QModelIndex&, const QModelIndex&)"), current,  previous)
    
    def sendViewNodeSourceSignal(self):
        index = self.currentIndex()
        
        if index.isValid():
            proxyModel = index.model()
            sourceIndex = proxyModel.mapToSource(index)
            
            self.emit(QtCore.SIGNAL("viewNodeSource(const QModelIndex&)"), sourceIndex)
    
class Civ4FilterWidget(QtGui.QWidget):
    def __init__(self, parent = None, treeView = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.treeView = treeView
        self.proxyModel = treeView.model()
        
        self.mainLayout = QtGui.QGridLayout(self)
        self.setLayout(self.mainLayout)
    
        self.filterPatternLineEdit = QtGui.QLineEdit(self)

        self.filterSyntaxComboBox = QtGui.QComboBox(self)
        self.filterSyntaxComboBox.addItem("Regular expression", QtCore.QVariant(QtCore.QRegExp.RegExp))
        self.filterSyntaxComboBox.addItem("Wildcard", QtCore.QVariant(QtCore.QRegExp.Wildcard))
        self.filterSyntaxComboBox.addItem("Fixed string", QtCore.QVariant(QtCore.QRegExp.FixedString))
        
        self.filterColumnComboBox = QtGui.QComboBox(self)
        self.filterColumnComboBox.addItem(self.tr('All'))
        
        self.sortCaseSensitivityCheckBox = QtGui.QCheckBox("Case sensitive sorting", self)
        self.filterCaseSensitivityCheckBox = QtGui.QCheckBox("Case sensitive filter", self)
        
        self.mainLayout.addWidget(self.filterPatternLineEdit, 0, 0, 1, -1)
        self.mainLayout.addWidget(self.filterSyntaxComboBox, 1, 0, 1, -1)
        self.mainLayout.addWidget(self.filterColumnComboBox, 2, 0, 1, -1)
        self.mainLayout.addWidget(self.filterCaseSensitivityCheckBox, 3, 0)
        self.mainLayout.addWidget(self.sortCaseSensitivityCheckBox, 3, 1)
        
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        
        self.connect(self.filterPatternLineEdit, QtCore.SIGNAL('textChanged(const QString &)'), self.filterRegExpChanged)
        self.connect(self.filterSyntaxComboBox, QtCore.SIGNAL('currentIndexChanged(int)'), self.filterRegExpChanged)
        self.connect(self.filterColumnComboBox, QtCore.SIGNAL('currentIndexChanged(int)'), self.filterColumnChanged)
        self.connect(self.filterCaseSensitivityCheckBox, QtCore.SIGNAL('toggled(bool)'), self.filterRegExpChanged)
        self.connect(self.sortCaseSensitivityCheckBox, QtCore.SIGNAL('toggled(bool)'), self.sortChanged)
    
    def setProxyModel(self):
        self.proxyModel = self.treeView.model()
        
    def updateColumnItem(self):
        for i in range(self.filterColumnComboBox.count() - 1):
            self.filterColumnComboBox.removeItem(1)
            
        headerView = self.treeView.header()
        model = self.treeView.model()
        
        for i in range(headerView.count()):
            data = model.headerData(i, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
            self.filterColumnComboBox.addItem(data.toString())

    def filterRegExpChanged(self):
        syntax_nr, _ = self.filterSyntaxComboBox.itemData(self.filterSyntaxComboBox.currentIndex()).toInt()
        syntax = QtCore.QRegExp.PatternSyntax(syntax_nr)

        if self.filterCaseSensitivityCheckBox.isChecked():
            caseSensitivity = QtCore.Qt.CaseSensitive
        else:
            caseSensitivity = QtCore.Qt.CaseInsensitive

        regExp = QtCore.QRegExp(self.filterPatternLineEdit.text(), caseSensitivity, syntax)
        self.proxyModel.setFilterRegExp(regExp)

    def filterColumnChanged(self):
        self.proxyModel.setFilterKeyColumn(self.filterColumnComboBox.currentIndex() - 1)

    def sortChanged(self):
        if self.sortCaseSensitivityCheckBox.isChecked():
            caseSensitivity = QtCore.Qt.CaseSensitive
        else:
            caseSensitivity = QtCore.Qt.CaseInsensitive

        self.proxyModel.setSortCaseSensitivity(caseSensitivity)
    
class Civ4TreeViewBundle(QtGui.QWidget):
    def __init__(self, parent = None, treeView = None, filterWidget = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.bundleLayout = QtGui.QVBoxLayout(self)
        self.setLayout(self.bundleLayout)
        
        self.bundleLayout.addWidget(filterWidget)
        self.bundleLayout.addWidget(treeView)
    
class Civ4TabBar(QtGui.QTabBar):
    def __init__(self, parent):
        QtGui.QTabBar.__init__(self)
        
    def mouseDoubleClickEvent(self, event):
        index = self.currentIndex()
        if index >= 0:
            self.emit(QtCore.SIGNAL("doubleClicked(const int&)"), index)
            event.accept()
        else:
            return QtGui.QTabBar.mouseDoubleClickEvent(self, event)
    
class Civ4XmlBaseWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.gridLayout = QtGui.QGridLayout(self)
        self.setLayout(self.gridLayout)
        
        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal, self)
        self.gridLayout.addWidget(self.splitter)
        
        self.splitterL = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.splitterR = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.splitter.addWidget(self.splitterL)
        self.splitter.addWidget(self.splitterR)
        
        self.leaderTagTreeView = Civ4TreeView(self)
        self.infoTreeView = Civ4TreeView(self)
        self.tagQueryTreeView = Civ4TreeView(self)
        
        #self.leaderTagTreeView.setToolTip(self.tr("LeaderTag TreeView"))
        #self.infoTreeView.setToolTip(self.tr("Info TreeView"))
        #self.tagQueryTreeView.setToolTip(self.tr("Tag Query TreeView"))
        
        self.leaderTagFilter = Civ4FilterWidget(self, self.leaderTagTreeView)
        self.infoFilter = Civ4FilterWidget(self, self.infoTreeView)
        self.tagQueryFilter = Civ4FilterWidget(self, self.tagQueryTreeView)
        
        self.leaderTagBundle = Civ4TreeViewBundle(self, self.leaderTagTreeView, self.leaderTagFilter)
        self.infoBundle = Civ4TreeViewBundle(self, self.infoTreeView, self.infoFilter)
        self.tagQueryBundle = Civ4TreeViewBundle(self, self.tagQueryTreeView, self.tagQueryFilter)
        
        self.infoTextBrowser = QtGui.QTextBrowser(self)
        self.infoTextBrowser.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        
        self.splitterL.addWidget(self.leaderTagBundle)
        self.splitterL.addWidget(self.infoTextBrowser)
        self.splitterR.addWidget(self.infoBundle)
        self.splitterR.addWidget(self.tagQueryBundle)

class Civ4XmlTabWidget(QtGui.QTabWidget):
    def __init__(self, parent = None):
        QtGui.QTabWidget.__init__(self, parent)
        
        self.civ4TabBar = Civ4TabBar(self)
        self.setTabBar(self.civ4TabBar)
        
        self.setAcceptDrops(True) 
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event): 
        urlList = event.mimeData().urls()
        
        if urlList:
            for url in urlList:
                filePath = url.toLocalFile()
                
                if filePath:
                    fileInfo = QtCore.QFileInfo(filePath)
                    
                    if fileInfo.isFile() and fileInfo.suffix() == 'xml' or fileInfo.isDir():
                        self.emit(QtCore.SIGNAL("openFileFromTabWidgetDropEvent(const QString &)"), filePath)

class Civ4XmlSourceViewWidget(QtGui.QMainWindow):
    def __init__(self, parent = None, iId = 0):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.iId = iId
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        ## menu
        self.menuFile = self.menuBar().addMenu(self.tr("&File")) 
        self.actionSaveAs = self.menuFile.addAction(self.tr("Save as..."), self.saveAs)
        
        self.menuView = self.menuBar().addMenu(self.tr("&View")) 
        self.actionSwitchFormat = self.menuView.addAction(self.tr("RichText"), self.switchFormat)
        self.actionSwitchFormat.setCheckable(True)
        
        self.toolBarFile = QtGui.QToolBar(self)
        self.toolBarFile.setWindowTitle(self.tr("File"))
        self.toolBarFile.addAction(self.actionSaveAs)
        self.addToolBar(self.toolBarFile)
        
        self.myCentralWidget = QtGui.QWidget()
        self.setCentralWidget(self.myCentralWidget)
        
        self.vLayout = QtGui.QVBoxLayout(self.myCentralWidget)
        self.myCentralWidget.setLayout(self.vLayout)
        
        self.sourceTextEdit = QtGui.QTextEdit(self)
        self.vLayout.addWidget(self.sourceTextEdit)
        
        self.sourceTextEdit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        
        self.setGeometry(100, 100, 800, 600)
    
    def setNode(self, node):
        text = QtCore.QString()
        out = QtCore.QTextStream(text)
        node.save(out, 4) 
        
        self.contents = text
        self.sourceTextEdit.setPlainText(text)
        
        if node.isDocument():
            self.setWindowTitle(node.documentElement().nodeName())
        else:
            self.setWindowTitle(node.nodeName())
    
    def setPlainTextToTextEdit(self, text):
        self.contents = text
        self.setWindowTitle(self.tr("Query Result"))
        self.sourceTextEdit.setPlainText(text)
    
    def setHelpContents(self, text):
        self.filePath = GC.g_appName
        self.contents = text
        self.setWindowTitle(self.tr("Help"))
        
        self.sourceTextEdit.setReadOnly(True)
        self.sourceTextEdit.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        self.sourceTextEdit.setText(text)
    
    def closeEvent(self, event):
        if self.iId:
            self.emit(QtCore.SIGNAL("sourceViewWidgetClosing(int)"),  self.iId)
        
        QtGui.QWidget.closeEvent(self, event)
    
    def saveAs(self):
        dirName = QtCore.QFileInfo(self.filePath).absolutePath()
        filePath = QtGui.QFileDialog.getSaveFileName(self, QtCore.QString(), dirName, self.tr("Text files (*.txt);;All files (*.*)"))
        
        if not filePath.isEmpty():
            saveFile = QtCore.QFile(filePath)
            
            if not saveFile.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                QtGui.QMessageBox.warning(self, self.tr("Codecs"), self.tr("Cannot write file %1:\n%2").arg(filePath).arg(saveFile.errorString()))
                return
            
            out = QtCore.QTextStream(saveFile)
            out << self.contents
            out.flush()
            saveFile.close()
    
    def switchFormat(self):
        if self.actionSwitchFormat.isChecked():
            self.sourceTextEdit.setText(self.contents)
        else:
            self.sourceTextEdit.setPlainText(self.contents)

class Civ4XmlMessageBox(QtGui.QMessageBox):
    def __init__(self, parent = None):
        QtGui.QMessageBox.__init__(self, parent)
        
        self.addButton(QtGui.QMessageBox.Ok)
        self.setIcon(QtGui.QMessageBox.Information)
        self.setTextFormat(QtCore.Qt.RichText)
    
    def setup(self, getter):
        title,  content = getter()
        
        self.setWindowTitle(self.tr(title))
        self.setText(content)

    def getAbout(self):
        title = u'Civ4 XML View Information'
        
        textList = QtCore.QStringList()
        
        textList.append(self.tr(u'Home Page :  %1').arg(u'<a href="http://code.google.com/p/civ4xml/">http://code.google.com/p/civ4xml/</a><br>'))
        textList.append(self.tr(u'Civ4 XML View version %1<br>').arg(GC.VERSION_civ4xml))
        textList.append(self.tr(u'Python version %1').arg(sys.version.split(u' ')[0]))
        textList.append(self.tr(u'PyQt version %1').arg(QtCore.PYQT_VERSION_STR))
        
        return title, textList.join(u'<br>')

    def getLicense(self):
        title = u'License'
        
        textList = QtCore.QStringList()
        textList.append(self.tr(u'<b>GNU GENERAL PUBLIC LICENSE</b>'))
        textList.append(self.tr(GC.TEXT_license))
        
        return title, textList.join(u'<br>')

class Civ4DirTreeView(QtGui.QTreeView):
    def __init__(self, parent = None):
        QtGui.QTreeView.__init__(self, parent)
        
        self.openFilePath = u''
        
        self.setDragEnabled(True)
        
        nameFilters = QtCore.QStringList()
        filters = QtCore.QDir.AllEntries | QtCore.QDir.NoDotAndDotDot
        sortFlags = QtCore.QDir.DirsFirst | QtCore.QDir.Type
        self.dirModel = QtGui.QDirModel(nameFilters, filters, sortFlags, self)
        #self.dirModel = Civ4DirModel(nameFilters, filters, sortFlags, self)
        self.setModel(self.dirModel)
    
        self.contextMenu = QtGui.QMenu(self)
        self.actionOpen = self.contextMenu.addAction(self.tr("Open"), self.open)
        
        self.connect(self, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.load)
        #self.connect(self, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.load)
    
    def getContextMenu(self):
        return self.contextMenu
    
    ## virtual protected
    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        self.setCurrentIndex(index)
        
        if index.isValid():
            fileInfo = self.model().fileInfo(index)
            if fileInfo.isFile() and fileInfo.suffix() == 'xml' or fileInfo.isDir():
                self.openFilePath = self.model().filePath(index)
                self.actionOpen.setText(self.tr('Open %1').arg(self.openFilePath))
                self.contextMenu.exec_(event.globalPos()) 

    ## SLOT
    def open(self):
        index = self.currentIndex()
        
        if index.isValid():
            fileInfo = self.model().fileInfo(index)
            if fileInfo.isFile() and fileInfo.suffix() == 'xml' or fileInfo.isDir():
                self.openFilePath = self.model().filePath(index)
                self.emit(QtCore.SIGNAL("openFileFromDirTreeView(const QString &)"), self.openFilePath)

    def load(self):
        index = self.currentIndex()
        
        if index.isValid():
            fileInfo = self.model().fileInfo(index)
            if fileInfo.isFile() and fileInfo.suffix() == 'xml':
                self.openFilePath = self.model().filePath(index)
                self.emit(QtCore.SIGNAL("loadFileFromDirTreeView(const QString &)"), self.openFilePath)
            elif  fileInfo.isDir():
                self.openFilePath = self.model().filePath(index)
                self.emit(QtCore.SIGNAL("openFileFromDirTreeView(const QString &)"), self.openFilePath)

class Civ4BookmarksTreeView(QtGui.QTreeView):
    def __init__(self, parent = None):
        QtGui.QTreeView.__init__(self, parent)
        
        self.openFilePath = u''

        self.bookmarksItemDelegate = Civ4NoProxyItemDelegate(self)
        self.setItemDelegate(self.bookmarksItemDelegate)
        
        self.setEditTriggers(QtGui.QAbstractItemView.EditKeyPressed)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        
        self.bookmarksModel = Civ4BookmarksModel(self)
        self.setModel(self.bookmarksModel)

        self.contextMenu = QtGui.QMenu(self)
        self.actionOpen = self.contextMenu.addAction(self.tr("Open"), self.open)
        self.actionAddFolder = self.contextMenu.addAction(self.tr("Add Folder"), self.addFolder)
        self.actionTriggerEditor = self.contextMenu.addAction(self.tr("Edit"), self.triggerEditor)
        self.actionRemove = self.contextMenu.addAction(self.tr("Remove"), self.remove)
        
        self.connect(self, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.load)
        #self.connect(self, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.load)
    
    def getContextMenu(self):
        return self.contextMenu
    
    ## virtual protected
    def contextMenuEvent(self, event):
        bValid = False
        bFolder = False
        self.actionOpen.setVisible(False)
        self.actionAddFolder.setVisible(False)
        self.actionTriggerEditor.setVisible(False)
        self.actionRemove.setVisible(False)
        
        index = self.indexAt(event.pos())
        self.setCurrentIndex(index)
        
        if index.isValid():
            item = index.internalPointer()
            fileInfo = QtCore.QFileInfo(item.getPath())
            
            if fileInfo.isFile() and fileInfo.suffix() == 'xml' or fileInfo.isDir():
                self.openFilePath = fileInfo.absoluteFilePath()
                self.actionOpen.setText(self.tr('Open %1').arg(self.openFilePath))
                self.actionOpen.setVisible(True)
                bValid = True
            
            if item.isFolder():
                bFolder = True
                if index.column() == 0:
                    self.actionTriggerEditor.setVisible(True)
                    bValid = True
            elif item.isFile() or item.isDir():
                if index.column() == 0 or index.column() == 1:
                    self.actionTriggerEditor.setVisible(True)
                    bValid = True
            
            if item.isBookmark():
                self.actionRemove.setVisible(True)
                self.actionRemove.setText(self.tr('Remove %1').arg(item.getName()))
                bValid = True
        
        else:
            bFolder = True
        
        if bFolder:
            bValid = True
            self.actionAddFolder.setVisible(True)
        
        if bValid:
            self.contextMenu.exec_(event.globalPos()) 

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-bookmarksdatalist") or event.mimeData().hasFormat("text/uri-list"):
            event.accept()
            self.setState(QtGui.QAbstractItemView.DraggingState)
        else:
            event.ignore()

    ## SLOT
    def open(self):
        index = self.currentIndex()
        
        if index.isValid():
            item = index.internalPointer()
            fileInfo = QtCore.QFileInfo(item.getPath())
            
            if fileInfo.isFile() and fileInfo.suffix() == 'xml':
                self.openFilePath = fileInfo.absoluteFilePath()
                self.emit(QtCore.SIGNAL("openFileFromBookmarksTreeView(const QString &, bool)"), self.openFilePath, False)
            elif fileInfo.isDir() and item.isDir():
                self.openFilePath = fileInfo.absoluteFilePath()
                self.emit(QtCore.SIGNAL("openFileFromBookmarksTreeView(const QString &, bool)"), self.openFilePath, True)

    def load(self):
        index = self.currentIndex()
        
        if index.isValid():
            item = index.internalPointer()
            fileInfo = QtCore.QFileInfo(item.getPath())
            
            if fileInfo.isFile() and fileInfo.suffix() == 'xml':
                self.openFilePath = fileInfo.absoluteFilePath()
                self.emit(QtCore.SIGNAL("loadFileFromBookmarksTreeView(const QString &)"), self.openFilePath)
            elif  fileInfo.isDir() and item.isDir():
                self.openFilePath = fileInfo.absoluteFilePath()
                self.emit(QtCore.SIGNAL("openFileFromBookmarksTreeView(const QString &, bool)"), self.openFilePath, True)
    
    def addFolder(self):
        row = -1
        parent = self.currentIndex()
        bookmarkNode = self.model().getNode(u'new folder', u'', u'folder')
        
        self.model().insertBookmark(row,  parent,  bookmarkNode)
    
    def triggerEditor(self):
        self.edit(self.currentIndex())
    
    def remove(self):
        self.model().removeBookmark(self.currentIndex())
        self.reset()
