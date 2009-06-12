#!/usr/bin/env python
# -*- coding: utf-8 -*-
# civ4xml_parser.py

from PyQt4 import QtCore, QtGui, QtXml

from civ4xml_constants import GC
import civ4xml_utilities as gu

class Civ4Xml(QtXml.QDomDocument):
    def __init__(self, filePath):
        QtXml.QDomDocument.__init__(self)

        f = QtCore.QFile(filePath)
        message = [False]
        if f.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            message = self.setContent(f)
        f.close()

        #assert message[0], 'domDocument setContent failed'
        #assert not self.isNull(),  'domDocument is null'
        
        if not message[0] or self.isNull():
            self.bXmlFail = True
            return
        else:
            if self.documentElement().childNodes().count() == 0:
                self.bXmlFail = True
                return
            else:
                self.bXmlFail = False
        
        self.root = self.documentElement()
        self.filePath = filePath
        self.schemaFileName = self.getSchemaFileName()
        self.schema = self.getSchema()

    def getSchemaFileName(self):
        attributes = self.root.attributes()
        if attributes.size():
            xmlns = attributes.item(0)
            if xmlns.nodeName() == GC.XML_xmlns:
                text = xmlns.nodeValue()
                if text.startsWith(u'x-schema:'):
                    return text.split(u'x-schema:')[-1]
        
        return u''
    
    def getSchema(self):
        if self.schemaFileName:
            xmlFileInfo = QtCore.QFileInfo(self.filePath)
            currentDir = xmlFileInfo.absoluteDir()
            schemaTargetFileInfo = QtCore.QFileInfo(currentDir, self.schemaFileName)
            schemaTargetFilePath = schemaTargetFileInfo.absoluteFilePath()
            
            result = gu.searchXml(schemaTargetFilePath)
            if result:
                schemaFilePath = result[0]
                return Civ4SchemaDict(schemaFilePath)
                
            else:
                print 'schema not found', self.schemaFileName
        
        return None
    
    def rootNode(self):
        return self.root
        
    def getBranchList(self):
        branchList = []
        flag = u''
        
        children = self.elementsByTagName(GC.LEADERTAG_FLAG_Type)
        trunk = self.root.firstChildElement()
        item = Civ4DomItem(trunk)
        
        ## CIV4XXXXinfos.xml
        if children.size() != 0:
            bCheckNodeName = False
            if item.isInfosTag(bCheckNodeName):
                flag = GC.LEADERTAG_FLAG_Type
        ## CIV4RouteModelInfos.xml
        elif item.isInfosTag():
            flag = GC.LEADERTAG_FLAG_Infos
        ## GlobalDefines.xml, CIV4GameText_BTS.xml, Schema, etc.
        else:
            trunk = self.root
            item = Civ4DomItem(trunk)
        
        if flag != GC.LEADERTAG_FLAG_Type and flag != GC.LEADERTAG_FLAG_Infos:
            if item.childElementsState() < 2:
                flag = GC.LEADERTAG_FLAG_Repeated
            else:
                flag = GC.LEADERTAG_FLAG_Different
                    
        return item.childElements(), flag  ## QDomNode-list, unicode
    
class Civ4SchemaDict(object):
    def __init__(self, filePath):
        self.filePath = filePath
        
        if not GC.VERSION_schema:
            return

        self.schemaDocument = QtXml.QDomDocument()
        self.hierarchyDict = {}
        ## hierarchyDict[tagname] = 
        ## { u'parent': parentList, u'children' : childList, u'attributes' : attributeList, u'elementMap' : elementDefinitionDict, u'attributeMap': attributeDefinitionDict, u'indicators': optional}
        ## childList[i] = (child, minOccurs, maxOccurs)
        
        f = QtCore.QFile(filePath)
        message = [False]
        if f.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            message = self.schemaDocument.setContent(f)
        f.close()

        #assert message[0], 'schema setContent failed'
        #assert not self.schemaDocument.isNull(), 'schema is null'
        
        if not message[0] or self.schemaDocument.isNull():
            return
        
        root = self.schemaDocument.documentElement()
        elementTypeNodes = root.childNodes()
        
        for i in range(elementTypeNodes.size()):
            elementType = elementTypeNodes.item(i)
            
            if elementType.isElement():
                assert unicode(elementType.nodeName()) == GC.SCHEMA_ElementType, 'schema format error'
                
                attributeMap = elementType.attributes()
                name = self.getAttribute(attributeMap, GC.SCHEMA_name)
                content = self.getAttribute(attributeMap, GC.SCHEMA_content)
                dt_type = self.getAttribute(attributeMap, GC.SCHEMA_dt_type)  ## dt:type
                
                if name not in self.hierarchyDict:
                    self.hierarchyDict[name] = {}
                if GC.HIERARCHY_parent not in self.hierarchyDict[name]:
                    self.hierarchyDict[name][GC.HIERARCHY_parent] = []
                self.hierarchyDict[name][GC.HIERARCHY_children] = []
                self.hierarchyDict[name][GC.HIERARCHY_attributes] = []
                self.hierarchyDict[name][GC.HIERARCHY_elementMap] = {}
                self.hierarchyDict[name][GC.HIERARCHY_attributeMap] = {}
                
                self.hierarchyDict[name][GC.HIERARCHY_elementMap][GC.SCHEMA_content] = content
                self.hierarchyDict[name][GC.HIERARCHY_elementMap][GC.SCHEMA_dt_type] = dt_type
                
                if not elementType.firstChildElement().isNull():
                ## elementType has real children
                
                    elementNodes = elementType.childNodes()
                    
                    for j in range(elementNodes.size()):
                        element = elementNodes.item(j)
                        
                        if element.isElement():
                            elementName = unicode(element.nodeName())
                            attributeMap = element.attributes()
                            
                            if elementName == GC.SCHEMA_element:
                                typeName = self.getAttribute(attributeMap, GC.SCHEMA_type)
                                minOccurs = self.getAttribute(attributeMap, GC.SCHEMA_minOccurs)
                                maxOccurs = self.getAttribute(attributeMap, GC.SCHEMA_maxOccurs)
                                
                                if typeName not in self.hierarchyDict:
                                    self.hierarchyDict[typeName] = {}
                                if GC.HIERARCHY_parent not in self.hierarchyDict[typeName]:
                                    self.hierarchyDict[typeName][GC.HIERARCHY_parent] = []
                                self.hierarchyDict[typeName][GC.HIERARCHY_parent].append(name)
                                
                                self.hierarchyDict[name][GC.HIERARCHY_children].append((typeName, minOccurs, maxOccurs))
                            
                            elif elementName == GC.SCHEMA_group:
                                if GC.HIERARCHY_indicators not in self.hierarchyDict[name]:
                                    self.hierarchyDict[name][GC.HIERARCHY_indicators] = []
                                
                                indicator = {}
                                order = self.getAttribute(attributeMap, GC.SCHEMA_order)
                                minOccurs = self.getAttribute(attributeMap, GC.SCHEMA_minOccurs)
                                maxOccurs = self.getAttribute(attributeMap, GC.SCHEMA_maxOccurs)
                                
                                indicator[GC.SCHEMA_order] = order
                                indicator[GC.SCHEMA_minOccurs] = minOccurs
                                indicator[GC.HIERARCHY_elements] = []
                                
                                indicatorElements = element.childNodes()
                                for k in range(indicatorElements.size()):
                                    indicatorElement = indicatorElements.item(k)
                                    if indicatorElement.isElement():
                                        if unicode(indicatorElement.nodeName()) == GC.SCHEMA_element:
                                            indicatorElementName = self.getAttribute(indicatorElement.attributes(), GC.SCHEMA_type)
                                            indicator[GC.HIERARCHY_elements].append(indicatorElementName)
                                            self.hierarchyDict[name][GC.HIERARCHY_children].append((indicatorElementName, minOccurs, maxOccurs))
                                            
                                print 'special element group'
                            
                            elif elementName == GC.SCHEMA_AttributeType:
                                attributeTypeName = self.getAttribute(attributeMap, GC.SCHEMA_name)
                                required = self.getAttribute(attributeMap, GC.SCHEMA_required)
                                self.hierarchyDict[name][GC.HIERARCHY_attributeMap][GC.SCHEMA_name] = attributeTypeName
                                self.hierarchyDict[name][GC.HIERARCHY_attributeMap][GC.SCHEMA_required] = required
                                print 'special element AttributeType'
                                
                            elif elementName == GC.SCHEMA_attribute:
                                attributeName = self.getAttribute(attributeMap, GC.SCHEMA_type)
                                self.hierarchyDict[name][GC.HIERARCHY_attributes].append(attributeName)
                                print 'special element attribute'
                            
                            else:
                                print 'unidentified element'
    
    def isNull(self):
        return bool(self.hierarchyDict)
    
    def getAttribute(self, attributeMap, name):
        attributeNode = attributeMap.namedItem(name)
        
        if attributeNode.isNull():
            return u''
        else:
            return unicode(attributeNode.nodeValue())
    
    def getParent(self, name):
        assert name in self.hierarchyDict, 'name not in hierarchyDict'
        
        return self.hierarchyDict[name][GC.HIERARCHY_parent]
    
    def getChildren(self, name):
        assert name in self.hierarchyDict, 'name not in hierarchyDict'
        
        return self.hierarchyDict[name][GC.HIERARCHY_children]
    
    def hasChild(self, name, child = None):
        assert name in self.hierarchyDict, 'name not in hierarchyDict'
        
        if child == None:
            return len(self.hierarchyDict[name][GC.HIERARCHY_children])
        else:
            for childTuple in self.hierarchyDict[name][GC.HIERARCHY_children]:
                if child == childTuple[0]:
                    return True
            return False
    
    def hasParent(self, name, parent = None):
        assert name in self.hierarchyDict, 'name not in hierarchyDict'
        
        if parent == None:
            return len(self.hierarchyDict[name][GC.HIERARCHY_parent])
        else:
            return parent in self.hierarchyDict[name][GC.HIERARCHY_parent]


class Civ4DomItem(QtXml.QDomNode):
    def __init__(self, node, position = (0,0), parent = None, generation = 0):
        QtXml.QDomNode.__init__(self, node)
        
        self.domNode = node
        ## Record the item's location within its parent.
        self.rowNumber, self.columnNumber = position
        self.generation = generation
        self.parentItem = parent  ## Civ4DomItem instance
        
        self.childItems = {}  ## int-Civ4DomItem dict
        self.root = self.ownerDocument().documentElement()
        
    def node(self):
        return self.domNode

    def parent(self):
        return self.parentItem

    def child(self, i = None, j = None):
        if i == None:
            i = self.rowNumber
        if j == None:
            j = self.columnNumber
            
        if self.isParentOfText():
            return None
        
        if self.childItems.has_key(i):
            return self.childItems[i]

        if i >= 0 and i < self.childNodes().size():
            childNode = self.childNodes().item(i)
            childItem = Civ4DomItem(childNode, (i, j), self, self.generation + 1)
            self.childItems[i] = childItem
            return childItem

        return None

    def row(self):
        return self.rowNumber
    
    def column(self):
        return self.columnNumber

    def setValueText(self, text):
        assert self.isParentOfText(), 'wrong call, node is not ParentOfText'
        
        if self.hasChildNodes():
            if text:
                self.firstChild().setNodeValue(text)
            else:
                self.removeChild(self.firstChild())
            
        elif text:
            textNode = self.ownerDocument().createTextNode(text)
            self.node().appendChild(textNode)
        
    def valueText(self):
        assert self.isParentOfText(), 'wrong call, node is not ParentOfText'
        
        if self.childNodes().size():
            return self.firstChild().nodeValue()
        
        return self.nodeValue() ## QString('')
        
    def attributesText(self):
        attributes = QtCore.QStringList()
        attributeMap = self.attributes()
        
        for i in range(attributeMap.size()):
            attribute = attributeMap.item(i)
            attributes.append(attribute.nodeName() + "=\"" + attribute.nodeValue() + "\"")
            
        return attributes.join(" ")
    
    def fullname(self):
        return self.nodeName() + QtCore.QString(u' ') + self.attributesText()
    
    def value(self):
        if self.isParentOfText():
            if not self.valueText().isEmpty():
                return self.valueText()
        
        return self.fullname()

    def getGeneration(self):
        child = self.domNode
        if not child.isElement() and not child.isComment() :
            return -1
            
        i = 0
        while True:
            if child == self.root:
                return i
            else:
                i += 1
                child = child.parentNode()        
    
    def childElements(self):
        children = []
        
        child = self.firstChildElement()
            
        while not child.isNull():
            children.append(child)
            child = child.nextSiblingElement()
            
        return children  ## QDomNode-list

    def getChildElementItemByIndex(self, iIndex):
        return Civ4DomItem(self.childElements()[iIndex])
    
    def getPeerIndex(self):
        me = self.node()
        parentNode = me.parentNode()

        if parentNode.isNull():
            return -2
        
        iIndex = 0
        node = parentNode.firstChild()
        
        while True:
            if node == me:
                return iIndex
            else:
                iIndex += 1
                node = node.nextSibling()
                
    def getPeerElementIndex(self):
        if not self.isElement():
            return -1
        
        me = self.node()
        parentNode = me.parentNode()
        
        if parentNode.isNull():
            return -2
        
        iIndex = 0
        node = parentNode.firstChildElement()
        
        while True:
            if node == me:
                return iIndex
            else:
                iIndex += 1
                node = node.nextSiblingElement()
    
    def getHierarchyIndexList(self, ancestorNode):
        assert self.isDescendant(ancestorNode)
        
        hierarchyIndexList = []
        node = self.node()
        parentNode = node.parentNode()
        
        while node != ancestorNode:
            iIndex = Civ4DomItem(node).getPeerIndex()
            hierarchyIndexList.insert(0, iIndex)
            node = node.parentNode()
        
        return hierarchyIndexList
    
    def getHierarchyNameQStringList(self, ancestorNode):
        assert self.isDescendant(ancestorNode)
        
        node = self.node()
        parentNode = node.parentNode()
        hierarchyNameQStringLis = QtCore.QStringList(node.nodeName())
        
        while node != ancestorNode:
            node = node.parentNode()
            hierarchyNameQStringLis.insert(0, node.nodeName())
        
        return hierarchyNameQStringLis

    def isDescendant(self, ancestorNode):
        node = self.node()
        while not node.isNull():
            if node == ancestorNode:
                return True
            else:
                node = node.parentNode()
        
        return False
    
    def isAncestor(self, descendantNode):
        ancestorNode = self.node()
        while not descendantNode.isNull():
            if ancestorNode == descendantNode:
                return True
            else:
                descendantNode = descendantNode.parentNode()
        
        return False

    def childElementsState(self, bCheckAttributes=True):
        children = self.childElements()
        state = len(children)
        
        if state < 2:
            return state
        else:
            firstChildItem = Civ4DomItem(children[0])
            if firstChildItem.hasDifferentElementSibling(bCheckAttributes):
                return 2
            else:
                return 1

    def hasDifferentElementSibling(self, bCheckAttributes = False):
        myname = self.nodeName()
        me = self.node()
        node = self.parentNode().firstChildElement()
        
        while not node.isNull():
            if node != me:
                name = node.nodeName()
                if myname != name or (node.attributes().size() != 0 and bCheckAttributes):
                    return True
            
            node = node.nextSiblingElement()
        
        return False
            
    def isTag(self):
        if self.isElement():
            if self.getGeneration() > 0:
                return True
        return False

    def isParentOfText(self):
        if not self.isTag():
            return False
            
        children = self.childNodes()
        if children.size() == 1:
            childNode = children.item(0)
            if childNode.isText():
                return True

        elif children.size() == 0:
            if self.isElement():
                return True
            
        return False

    def isInfosTag(self, bCheckName=True):
        if self.isTag():
            if self.getGeneration() == 1 and self.nextSiblingElement().isNull() and self.previousSiblingElement().isNull():
                if self.childElementsState() == 0:
                    return True
                elif self.childElementsState() == 1:
                    if not bCheckName:
                        return True
                    else:
                        childname = unicode(self.firstChildElement().nodeName())
                        name = unicode(self.nodeName())
                        ## ex. infos, info
                        if name == childname + u's':
                            return True
                        ## ex. categories, category
                        else:
                            if name[:-3] == childname[:-2] and name[-3:] == u'ies' and name[-1] == u'y':
                                return True
        return False

    def isInfoTag(self, bCheckName=True):
        return Civ4DomItem(self.parentNode()).isInfosTag(bCheckName)
        
    def isChildOfInfoTag(self, bCheckName=False):
        return Civ4DomItem(self.parentNode()).isInfoTag(bCheckName)
    
    def isParentOfTagPair(self):
        if self.childElementsState(False) != 2:
            return False
        
        children = self.childElements()
        if len(children) > 2:
            return False
            
        for child in children:
            if not Civ4DomItem(child).isParentOfText():
                return False
        
        return True
    
    def getQueryTagItem(self):
        assert not self.isInfoTag(False)
        assert not self.isInfosTag(False)
        assert self.getGeneration() >= 2
        
        item = self
        while True:
            if item.isParentOfTagPair():
                return (item, GC.TAGQUERY_FLAG_TagPair)
                
            elif item.isChildOfInfoTag() or item.getGeneration() == 2:
                if item.isParentOfText():
                    return (item, GC.TAGQUERY_FLAG_Text)
                return (item, u'')
            
            item = Civ4DomItem(item.parentNode())
    
    def getBranchAncestor(self, flag = ''):
        assert not self.isInfoTag(False) and not self.isInfosTag(False) and self.getGeneration() >= 2
        
        if flag != GC.LEADERTAG_FLAG_Repeated and flag != GC.LEADERTAG_FLAG_Different:
            ## root - infos - info
            generation = 2
        else:
            ## root - tag
            generation = 1
        
        item = self
        while True:
            if item.getGeneration() == generation:
                return item.node()
            item = Civ4DomItem(item.parentNode())
    
    def getLeaderTag(self, flag = ''):
        branchAncestor = self.getBranchAncestor(flag)
            
        if flag == GC.LEADERTAG_FLAG_Different:
            return branchAncestor
        else:
            if flag != GC.LEADERTAG_FLAG_Type:
                flag = QtCore.QString()
                
            leaderTag = branchAncestor.firstChildElement(flag)
            if leaderTag.isNull():
                print 'Civ4DomItem, getLeaderTag', branchAncestor.nodeName()
                return branchAncestor
            else:
                return leaderTag
        
class Civ4LeaderTagModel(QtCore.QAbstractItemModel):
    def __init__(self, branchList, flag, parent=None):
        ## branchList is a List of QDomNode
        QtCore.QAbstractItemModel.__init__(self, parent)

        self.update(branchList, flag)
    
    def update(self, branchList, flag):
        self.leaderTagList = []
        self.flag = flag
        
        if flag == GC.LEADERTAG_FLAG_Type:
            for node in branchList:
                leaderTag = node.firstChildElement(flag)
                if leaderTag.isNull():
                    raise '<Type> missing error'
                    leaderTag = node
                self.leaderTagList.append(leaderTag)
        
        elif flag == GC.LEADERTAG_FLAG_Infos:
            for node in branchList:
                leaderTag = node.firstChildElement()
                if leaderTag.isNull():
                    raise 'no sub-tag in InfoTag'
                    leaderTag = node
                self.leaderTagList.append(leaderTag)
            
            if self.leaderTagList:
                self.flag = unicode(self.leaderTagList[0].nodeName())

        elif flag == GC.LEADERTAG_FLAG_Repeated:
            for node in branchList:
                leaderTag = node.firstChildElement()
                if leaderTag.isNull():
                    print 'no child'
                    leaderTag = node
                self.leaderTagList.append(leaderTag)
                
        elif flag == GC.LEADERTAG_FLAG_Different:
            self.leaderTagList = branchList
                
        else:
            raise 'leaderTagList error'
    
    def getLeaderTags(self):
        return (self.leaderTagList, self.flag)
    
    def getLeaderTagIndex(self,  rowNumber, columnNumber = 0):
        return self.index(rowNumber, columnNumber, QtCore.QModelIndex())

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 3

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        node = index.internalPointer()
        item = Civ4DomItem(node)
            
        if index.column() == 0:
            return QtCore.QVariant(item.nodeName())
        
        elif index.column() == 1:
            if self.flag != GC.LEADERTAG_FLAG_Different:
                text = item.value()
            else:
                text = item.fullname()
            return QtCore.QVariant(text)
        
        elif index.column() == 2:
            return QtCore.QVariant(index.row() + 1)

        else:
            return QtCore.QVariant()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
                
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                if self.flag != GC.LEADERTAG_FLAG_Different and self.flag != GC.LEADERTAG_FLAG_Repeated:
                    return QtCore.QVariant(self.tr(self.flag))
                else:
                    if self.leaderTagList:
                        return QtCore.QVariant(self.tr(self.leaderTagList[0].parentNode().nodeName()))
            elif section == 1:
                return QtCore.QVariant(self.tr("Value"))
            elif section == 2:
                return QtCore.QVariant(self.tr("#"))
            else:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            return self.createIndex(row, column, self.leaderTagList[row])
        else:
            return QtCore.QModelIndex()

    def parent(self, child):
        return QtCore.QModelIndex()

    def rowCount(self, parent = QtCore.QModelIndex()):
        if not parent.isValid():
            return len(self.leaderTagList)
        else:
            return 0

class Civ4DomModel(QtCore.QAbstractItemModel):
    ## document is a QDomNode
    def __init__(self, document, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)

        self.domDocument = document  ## QDomNode
        self.rootItem = Civ4DomItem(self.domDocument)
        self.leaderTagIndex = 0
    
    def update(self, document, index = 0):
        self.domDocument = document
        self.rootItem = Civ4DomItem(self.domDocument)
        self.leaderTagIndex = index

    def getIndexByItem(self, item, columnNumber = 0):
        if not item.isDescendant(self.rootItem.node()):
            return None
        
        hierarchyIndexList = item.getHierarchyIndexList(self.rootItem.node())
        index = QtCore.QModelIndex()
        
        for i in hierarchyIndexList:
            index = self.index(i, 0, index)
        
        if index.isValid():
            return index
        else:
            return None

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 4

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        
        item = index.internalPointer()

        if index.column() == 0:
            return QtCore.QVariant(item.nodeName())
        
        elif index.column() == 1:
            return QtCore.QVariant(item.attributesText())

        elif index.column() == 2:
            if item.isParentOfText():
                return QtCore.QVariant(item.valueText().split("\n").join(" "))
                
            return QtCore.QVariant(item.nodeValue().split("\n").join(" "))
        
        elif index.column() == 3:
            return QtCore.QVariant(index.row() + 1)
            
        else:
            return QtCore.QVariant()

    def setData(self, index, value, role = QtCore.Qt.EditRole): 
        if index.column() == 2 and role == QtCore.Qt.EditRole:
            item = index.internalPointer()
            
            if item.isParentOfText():
                if item.valueText() != value.toString():
                    item.setValueText(value.toString())
                    self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
                    self.emit(QtCore.SIGNAL("nodeTextChanged(const QModelIndex&)"),  index)
                    return True
        
        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        if index.column() == 2:
            item = index.internalPointer()
            if item.isParentOfText():
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable    

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant(self.tr("Name"))
            elif section == 1:
                return QtCore.QVariant(self.tr("Attributes"))
            elif section == 2:
                return QtCore.QVariant(self.tr("Value"))
            elif section == 3:
                return QtCore.QVariant(self.tr("#"))
            else:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        childItem = parentItem.child(row)
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, child):
        if not child.isValid():
            return QtCore.QModelIndex()

        childItem = child.internalPointer()
        parentItem = childItem.parent()

        if not parentItem or parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent = QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        if parentItem.isParentOfText():
            return 0
        
        return parentItem.childNodes().size()

class Civ4TagQueryModel(QtCore.QAbstractItemModel):
    def __init__(self, leaderTags, tags, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)

        self.update(leaderTags, tags)
        self.templateItem = None
        
    def update(self, leaderTags, tags, templateItem = None):
        self.tagList, self.tagFlag = tags
        self.leaderTagList, self.leaderTagFlag = leaderTags
        self.templateItem = templateItem
        
        self.leaderTagItemList = []
        self.tagItemList = []
        for i in range(len(self.leaderTagList)):
            self.leaderTagItemList.append(Civ4DomItem(self.leaderTagList[i], (i,0), self.leaderTagFlag))
            self.tagItemList.append(Civ4DomItem(self.tagList[i], (i,1)))
    
    def getLeaderTagIndex(self, index):
        if not index.isValid():
            return None
        
        while True:
            parent = index.parent()
            if parent.isValid():
                index = parent
            else:
                return index.sibling(index.row(), 2)
    
    def getRealItem(self, index):
        item = index.internalPointer()
        if self.tagFlag == GC.TAGQUERY_FLAG_TagPair:
            item = Civ4DomItem(item.lastChildElement())
            
        return item
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        if not parent.isValid():
            return 4
        
        return 2

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        
        item = index.internalPointer()
        
        if self.tagFlag == GC.TAGQUERY_FLAG_TagPair:
            if index.column() == 0:
                text = Civ4DomItem(item.firstChildElement()).valueText().split("\n").join(" ")
                return QtCore.QVariant(text)
                
            elif index.column() == 1:
                text = Civ4DomItem(item.lastChildElement()).valueText().split("\n").join(" ")
                return QtCore.QVariant(text)
        
        if not item.parent() or item.parent() == self.leaderTagFlag:
            if index.column() == 0:
                return QtCore.QVariant(item.nodeName())

            elif index.column() == 1:
                if item.isParentOfText():
                    text = item.valueText().split("\n").join(" ")
                else:
                    text = item.nodeValue().split("\n").join(" ")
                    
                return QtCore.QVariant(text)
                
            elif index.column() == 2:
                if self.leaderTagFlag != GC.LEADERTAG_FLAG_Different:
                    text = item.value()
                else:
                    text = item.fullname()
                return QtCore.QVariant(text)
            
            elif index.column() == 3:
                return QtCore.QVariant(index.row() + 1)
                
        else:
            if index.column() == 0:
                return QtCore.QVariant(item.nodeName())

            elif index.column() == 1:
                if item.isParentOfText():
                    return QtCore.QVariant(item.valueText().split("\n").join(" "))

                return QtCore.QVariant(item.nodeValue().split("\n").join(" "))
                
        return QtCore.QVariant()

    def setData(self, index, value, role = QtCore.Qt.EditRole): 
        if index.column() == 1 and role == QtCore.Qt.EditRole:
            item = index.internalPointer()
            
            if self.tagFlag == GC.TAGQUERY_FLAG_TagPair:
                if Civ4DomItem(item.lastChildElement()).valueText() != value.toString():
                    Civ4DomItem(item.lastChildElement()).setValueText(value.toString())
                    self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
                    self.emit(QtCore.SIGNAL("nodeTextChanged(const QModelIndex&)"),  index)
                    return True
                    
            elif item.isParentOfText():
                if item.valueText() != value.toString():
                    item.setValueText(value.toString())
                    self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"),  index,  index)
                    self.emit(QtCore.SIGNAL("nodeTextChanged(const QModelIndex&)"),  index)
                    return True
        
        return False
        
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        if index.column() == 1:
            item = index.internalPointer()
            if self.tagFlag == GC.TAGQUERY_FLAG_TagPair or item.isParentOfText():
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable    

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant(self.tr("Tag"))
            elif section == 1:
                return QtCore.QVariant(self.tr("Value"))
            elif section == 2:
                if self.leaderTagFlag != GC.LEADERTAG_FLAG_Different and self.leaderTagFlag != GC.LEADERTAG_FLAG_Repeated:
                    return QtCore.QVariant(self.tr(self.leaderTagFlag))
                else:
                    if self.leaderTagList:
                        return QtCore.QVariant(self.tr(self.leaderTagList[0].parentNode().nodeName()))
            elif section == 3:
                return QtCore.QVariant(self.tr("#"))
            else:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            if column == 2:
                return self.createIndex(row, column, self.leaderTagItemList[row])
            else:
                return self.createIndex(row, column, self.tagItemList[row])
         
        ## redundant, double check
        elif self.tagFlag == GC.TAGQUERY_FLAG_TagPair:
            return QtCore.QModelIndex()
            
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
            
    def parent(self, child):
        if not child.isValid():
            return QtCore.QModelIndex()
        
        childItem = child.internalPointer()  ## Civ4DomItem instance
        parentItem = childItem.parent()
        
        if not parentItem or parentItem == self.leaderTagFlag:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(parentItem.row(), 0, parentItem)
    
    def rowCount(self, parent = QtCore.QModelIndex()):
        if not parent.isValid():
            return len(self.tagList)
        else:
            if self.tagFlag == GC.TAGQUERY_FLAG_TagPair:
                return 0
                
            parentItem = parent.internalPointer()
            
            ## leaderTag
            if parentItem == self.leaderTagFlag:
                return 0
            ## tag
            else:
                if parent.column() != 0:
                    return 0

                if parentItem.isParentOfText():
                    return 0

                return parentItem.childNodes().size()


class Civ4InfoSortFilterProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent = None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
    
    def filterAcceptsRow (self, source_row, source_parent ):
        if not GC.INI_filter_deep:
            return QtGui.QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)

        model = self.sourceModel()
        source_child = model.index(source_row, 0, source_parent)
        
        if model.rowCount(source_child) == 0:
            return QtGui.QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)
        else:
            for i in range(model.rowCount(source_child)):
                    if self.filterAcceptsRow(i, source_child):
                        return True
        
        return False

class Civ4SortFilterProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent = None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
        self.setDynamicSortFilter(True)

    def filterAcceptsRow (self, source_row, source_parent ):
        if not GC.INI_filter_deep:
            return QtGui.QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)

        model = self.sourceModel()
        source_child = model.index(source_row, 0, source_parent)
        
        if model.rowCount(source_child) == 0:
            return QtGui.QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)
        else:
            for i in range(model.rowCount(source_child)):
                    if self.filterAcceptsRow(i, source_child):
                        return True
        
        return False

    def lessThan(self, left, right):
        ## TAGQUERY_ColumnNumber_value = 1
        if left.column() == 1 and right.column() == 1:
            dataLeft = left.data()
            dataRight = right.data()
            i, bi = dataLeft.toInt()
            j, bj = dataRight.toInt()
            
            if bi and bj:
                return i < j
                
        return QtGui.QSortFilterProxyModel.lessThan(self, left, right)
    
    def toHtml(self, rootIndex = QtCore.QModelIndex()): 
        if not self.rowCount(rootIndex):
            return u''
        
        tagColumn = GC.TAGQUERY_ColumnNumber_tag
        leaderTagColumn = GC.TAGQUERY_ColumnNumber_leaderTag
        valueColumn = GC.TAGQUERY_ColumnNumber_value

        TableItem = QtCore.QString(u'<td> %1 </td>')
        line1 = QtCore.QStringList()
        line2 = QtCore.QStringList()
        
        line1.append(u'<tr>')
        line2.append(u'<tr>')
        line1.append(TableItem.arg(u''))
        line2.append(TableItem.arg(self.data(self.index(0, tagColumn, rootIndex), QtCore.Qt.DisplayRole).toString()))
        
        for i in range(self.rowCount(rootIndex)):
            text1 = self.data(self.index(i, leaderTagColumn, rootIndex), QtCore.Qt.DisplayRole).toString()
            text2 = self.data(self.index(i, valueColumn, rootIndex), QtCore.Qt.DisplayRole).toString()
            line1.append(TableItem.arg(text1))
            line2.append(TableItem.arg(text2))
        
        line1.append(u'</tr>')
        line2.append(u'</tr>')
        
        output = QtCore.QStringList()
        output.append(u'<table>')
        output.append(line1.join(u''))
        output.append(line2.join(u''))
        output.append(u'</table>')
        
        return output.join(u'\n')
        
    def toHtmlStats(self, rootIndex = QtCore.QModelIndex()): 
        if not self.rowCount(rootIndex):
            return u''
        
        tagColumn = GC.TAGQUERY_ColumnNumber_tag
        leaderTagColumn = GC.TAGQUERY_ColumnNumber_leaderTag
        valueColumn = GC.TAGQUERY_ColumnNumber_value
        
        #TableItem = QtCore.QString(u'<td> %1 </td>')
        TableRow = QtCore.QString(u'<tr><td> %1 </td><td> %2 </td></tr>')
        statsDict = {}
        
        for i in range(self.rowCount(rootIndex)):
            typeName = self.data(self.index(i, leaderTagColumn, rootIndex), QtCore.Qt.DisplayRole).toString()
            key = self.data(self.index(i, valueColumn, rootIndex), QtCore.Qt.DisplayRole).toString()
            
            if key not in statsDict:
                statsDict[key] = QtCore.QStringList()

            statsDict[key].append(typeName)
        
        output = QtCore.QStringList()
        output.append(u'<table>')
        
        firstRow = TableRow.arg(self.data(self.index(0, tagColumn, rootIndex), QtCore.Qt.DisplayRole).toString()).arg(u'Type')
        output.append(firstRow)
        
        keys = statsDict.keys()
        keys.sort(gu.cmpTagValue)
        for key in keys:
            output.append(TableRow.arg(key).arg(statsDict[key].join(u', ')))
            
        output.append(u'</table>')
        
        return output.join(u'\n')

class Civ4DirModel(QtGui.QDirModel):
    def __init__(self, nameFilters = QtCore.QStringList(), filters = QtCore.QDir.Filters(), sort = QtCore.QDir.SortFlags(), parent = None):
        QtGui.QDirModel.__init__(self, nameFilters, filters, sort, parent)

class Civ4BookmarksItem(QtXml.QDomNode):
    def __init__(self, node,  parentItem = None):
        QtXml.QDomNode.__init__(self, node)
        
        self.domNode = node
        self.parentItem = parentItem
        
        self.init()
    
    def init(self):
        self.childItems = []
        children = self.childNodes()
        
        for i in range(children.count()):
            child = children.item(i)
            childItem = Civ4BookmarksItem(child, self)
            
            if childItem.isBookmark():
                self.childItems.append(childItem)
        
    def node(self):
        return self.domNode
    
    def parentItemBookmark(self):
        return self.parentItem
    
    def childItemBookmarks(self):
        return self.childItems
    
    def rowNumber(self):
        parentNode = self.node().parentNode()
        
        if parentNode.isNull():
            return -1
        else:
            i = 0
            child = parentNode.firstChild()
            
            while True:
                if child == self.domNode:
                    return i
                
                i += 1
                child = child.nextSibling()

    def isFolder(self):
        if self.nodeName() == u'folder':
            return True
        else:
            return False

    def isFile(self):
        if self.nodeName() == u'file':
            return True
        else:
            return False

    def isDir(self):
        if self.nodeName() == u'dir':
            return True
        else:
            return False
    
    def isBookmark(self):
        return self.isFile() or self.isDir() or self.isFolder()
    
    def getName(self):
        return self.firstChildElement(u'name').firstChild().nodeValue()
        
    def getPath(self):
        if self.isFile() or self.isDir():
            return self.firstChildElement(u'path').firstChild().nodeValue()
        else:
            return QtCore.QString()
    
    def getComments(self):
        if self.isFolder():
            return QtCore.QString(u'folder')
        elif self.isFile():
            return QtCore.QString(u'file')
        elif self.isDir():
            return QtCore.QString(u'dir')
        
        return QtCore.QString()
    
    def setName(self,  text):
        target = self.firstChildElement(u'name')
        
        if target.hasChildNodes():
            target.firstChild().setNodeValue(text)
            
        elif text:
            textNode = target.ownerDocument().createTextNode(text)
            target.appendChild(textNode)

    def setPath(self,  text):
        target = self.firstChildElement(u'path')
        
        if target.hasChildNodes():
            if text:
                target.firstChild().setNodeValue(text)
            
        elif text:
            textNode = target.ownerDocument().createTextNode(text)
            target.appendChild(textNode)

class Civ4BookmarksModel(QtCore.QAbstractItemModel):
    def __init__(self, parent = None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        
        self.filePath = GC.g_bookmarksFileInfo.absoluteFilePath()
        self.bModified = False
        self.iconProvider = QtGui.QFileIconProvider()
        
        self.loadXml()
        self.testBookmarks()
 
    def loadXml(self):
        self.domDocument = QtXml.QDomDocument()
        
        f = QtCore.QFile(self.filePath)
        message = [False]
        if f.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            message = self.domDocument.setContent(f)
        f.close()
        
        if not message[0] or self.domDocument.isNull():
            self.bXmlFail = True
        else:
            self.bXmlFail = False
            
        self.rootItem = Civ4BookmarksItem(self.domDocument.documentElement())

    def testBookmarks(self):
        if not self.rootItem.childItemBookmarks():
            for dirPath in [GC.g_XmlDir_Vanilla, GC.g_XmlDir_Wl, GC.g_XmlDir_BtS]:
                if dirPath:
                    self.insertBookmark(-1, QtCore.QModelIndex(), self.getNodeFromPath(dirPath))

    def isModified(self):
        return self.bModified

    def getRootItem(self):
        return self.rootItem

    def getNode(self, name, path, comments):
        bookmark = self.domDocument.createElement(comments)
        nameNode = self.domDocument.createElement(u'name')
        nameTextNode = self.domDocument.createTextNode(name)
        nameNode.appendChild(nameTextNode)
        bookmark.appendChild(nameNode)
        
        if comments == u'file' or comments == u'dir':
            pathNode = self.domDocument.createElement(u'path')
            pathTextNode = self.domDocument.createTextNode(path)
            pathNode.appendChild(pathTextNode)
            bookmark.appendChild(pathNode)
        
        return bookmark
    
    def getNodeFromPath(self,  filePath):
        fileInfo = QtCore.QFileInfo(filePath)
        if fileInfo.isDir():
            comments = u'dir'
        else:
            comments = u'file'

        return self.getNode(fileInfo.fileName(), fileInfo.absoluteFilePath(), comments)

    def insertBookmark(self, row, parent, bookmarkNode):
        if row == -1:
            first = self.rowCount(parent)
        else:
            first = row
        
        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            parentItem = self.rootItem

        bookmarkItem = Civ4BookmarksItem(bookmarkNode, parentItem)        

        self.beginInsertRows(parent, first, first)
        
        if row == -1:
            parentItem.node().appendChild(bookmarkNode)
        elif row == 0:
            refChild = parentItem.childItemBookmarks()[0].node()
            parentItem.node().insertBefore(bookmarkNode, refChild)
        else:
            refChild = parentItem.childItemBookmarks()[row -1].node()
            parentItem.node().insertAfter(bookmarkNode, refChild)
        
        parentItem.childItemBookmarks().insert(first, bookmarkItem)
        self.bModified = True

        self.endInsertRows()
    
    def removeBookmark(self, index):
        if not index.isValid():
            return
        
        parent = self.parent(index)
        row = index.row()
        item = index.internalPointer()
        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            parentItem = self.rootItem
        
        self.beginRemoveRows(parent, row, row) 
        parentItem.node().removeChild(item.node())
        del parentItem.childItemBookmarks()[row]
        self.bModified = True
        self.endRemoveRows() 

    def save(self):
        if not self.bModified:
            return

        saveFile = QtCore.QFile(self.filePath)
                
        if not saveFile.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            QtGui.QMessageBox.warning(self, self.tr("Codecs"), self.tr("Cannot write file %1:\n%2").arg(self.filePath).arg(saveFile.errorString()))
            return

        out = QtCore.QTextStream(saveFile)
        self.domDocument.save(out, 4)
        out.flush()
        saveFile.close()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled
        
        defaultFlags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
        flags = QtCore.Qt.NoItemFlags
        
        item = index.internalPointer()

        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsEditable
            if item.isFolder():
                flags |= QtCore.Qt.ItemIsDropEnabled
        elif index.column() == 1:
            if item.isFile() or item.isDir():
                flags |= QtCore.Qt.ItemIsEditable

        return defaultFlags | flags

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 3

    def rowCount(self, parent = QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        if parentItem.isFile() or parentItem.isDir():
            return 0
        else:
            return len(parentItem.childItemBookmarks())

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        return self.createIndex(row, column, parentItem.childItemBookmarks()[row])

    def parent(self, child):
        if not child.isValid():
            return QtCore.QModelIndex()
        
        childItem = child.internalPointer()
        parentItem = childItem.parentItemBookmark()

        if parentItem == self.rootItem or parentItem.node() == self.rootItem.node():
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.rowNumber(), 0, parentItem)

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant(self.tr("Name"))
            elif section == 1:
                return QtCore.QVariant(self.tr("Path"))
            elif section == 2:
                return QtCore.QVariant(self.tr("Comments"))
            else:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()
        
        item = index.internalPointer()
        
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0: 
                return QtCore.QVariant(item.getName().split("\n").join(" "))
            elif index.column() == 1:
                return QtCore.QVariant(item.getPath().split("\n").join(" "))
            elif index.column() == 2:
                return QtCore.QVariant(item.getComments().split("\n").join(" "))
            
        elif role == QtCore.Qt.ToolTipRole:
            if item.isFile() or item.isDir():
                return QtCore.QVariant(item.getPath().split("\n").join(" "))
            elif item.isFolder():
                text = QtCore.QString(u'%1 item')
                return QtCore.QVariant(self.tr(text.arg(len(item.childItemBookmarks()))))
            
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                if item.isFolder():
                    return QtCore.QVariant(self.iconProvider.icon(QtGui.QFileIconProvider.Trashcan))
                else:
                    return QtCore.QVariant(self.iconProvider.icon(QtCore.QFileInfo(item.getPath())))

        return QtCore.QVariant()

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if index.isValid() and role == QtCore.Qt.EditRole:
            item = index.internalPointer()
            
            if index.column() == 0:
                item.setName(value.toString())
                self.bModified = True
                return True
            elif index.column() == 1:
                item.setPath(value.toString())
                self.bModified = True
                return True

        return False
    
    def insertRows(self, row, count, parent = QtCore.QModelIndex()):
        if row < 0 or row > self.rowCount(parent) or count < 1:  # or parent.column() > 0:
            return False
        
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.endInsertRows()
        
        return True

    def mimeTypes(self):
        types = QtCore.QStringList()
        types << "application/x-bookmarksdatalist" << "text/uri-list"
        return types

    def mimeData(self, indexes):
        mimeData = QtCore.QMimeData()
        encodedData = QtCore.QByteArray()
        
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.WriteOnly)
        
        for index in indexes:
            if index.isValid():
                stream << self.data(index)

        mimeData.setData("application/x-bookmarksdatalist", encodedData)
        return mimeData
        
    def dropMimeData(self, data, action, row, column, parent):
        ok = False
        
        if data.hasFormat("application/x-bookmarksdatalist"):
            encodedData = data.data("application/x-bookmarksdatalist")
            stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.ReadOnly)
        
            while not stream.atEnd():
                c0 = QtCore.QVariant()
                c1 = QtCore.QVariant()
                c2 = QtCore.QVariant()
                stream >> c0 >> c1 >> c2
                name, path,  comments = c0.toString(),  c1.toString(),  c2.toString()
                ok = True
        
        elif data.hasFormat("text/uri-list"):
            urlList = data.urls()
            if urlList:
                for url in urlList:
                    filePath = url.toLocalFile()
                    if filePath:
                        fileInfo = QtCore.QFileInfo(filePath)
                        if fileInfo.isFile() and fileInfo.suffix() == 'xml':
                            name, path,  comments = fileInfo.fileName(), fileInfo.absoluteFilePath(), u'file'
                            ok = True
                        elif fileInfo.isDir():
                            name, path,  comments = fileInfo.fileName(), fileInfo.absoluteFilePath(), u'dir'
                            ok = True
        
        if ok:
            self.insertBookmark(row, parent,  self.getNode(name, path, comments))
            return True
        
        return False
    
    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction 
