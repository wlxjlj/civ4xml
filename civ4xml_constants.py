#!/usr/bin/env python
# -*- coding: utf-8 -*-
# civ4xml_constants.py

class GC(object):
    ## xml
    XML_xmlns = u'xmlns'

    ## schema
    SCHEMA_ElementType = u'ElementType'
    SCHEMA_element = u'element'
    SCHEMA_AttributeType = u'AttributeType'
    SCHEMA_attribute = u'attribute'
    SCHEMA_name = u'name'
    SCHEMA_content = u'content'
    SCHEMA_dt_type = u'dt:type'
    SCHEMA_type = u'type'
    SCHEMA_minOccurs = u'minOccurs'
    SCHEMA_maxOccurs = u'maxOccurs'
    SCHEMA_group = u'group'
    SCHEMA_order = u'order'
    SCHEMA_required = u'required'

    HIERARCHY_parent = u'parent'
    HIERARCHY_children = u'children'
    HIERARCHY_attributes = u'attributes'
    HIERARCHY_elementMap = u'elementMap'
    HIERARCHY_attributeMap = u'attributeMap'
    HIERARCHY_indicators = u'indicators'
    HIERARCHY_elements = u'elements'

    ## leaderTag 
    LEADERTAG_FLAG_Type = u'Type'
    LEADERTAG_FLAG_Infos = u'Infos'
    LEADERTAG_FLAG_Repeated = u'Repeated'
    LEADERTAG_FLAG_Different = u'Different'
    LEADERTAG_ColumnNumber_value = 1
    LEADERTAG_ColumnNumber_index = 2
    
    ## info
    INFO_ColumnNumber_value = 2
    INFO_ColumnNumber_index = 3
    
    ## tagQuery 
    TAGQUERY_FLAG_Text = u'Text'
    TAGQUERY_FLAG_TagPair = u'TagPair'
    TAGQUERY_ColumnNumber_tag = 0
    TAGQUERY_ColumnNumber_value = 1
    TAGQUERY_ColumnNumber_leaderTag = 2
    TAGQUERY_ColumnNumber_index = 3

    ## registry
    REG_ORGANIZATION_Firaxis = u'Firaxis Games'
    REG_APPLICATION_Vanilla = ur"Sid Meier's Civilization 4"
    REG_APPLICATION_Wl = ur"Sid Meier's Civilization 4 - Warlords"
    REG_APPLICATION_BtS = ur"Sid Meier's Civilization 4 - Beyond the Sword"
    REG_KEY_INSTALLDIR = u'INSTALLDIR'

    ## dir
    Dir_Xml = u'/Assets/XML'
    
    ## filename
    FileName_readme = u'readme.txt'
    FileName_bookmarks = u'bookmarks.xml'
    
    ## settings
    INI_FileBaseName = u'Civ4XML_settings'
    INI_FileName = u'Civ4XML_settings.ini'
    INI_DEFAULT_FileBaseName = u'Civ4XML_default_settings'
    INI_DEFAULT_FileName = u'Civ4XML_default_settings.ini'
    
    INI_GROUP_Path = u'Path'
    INI_path_startup_key = u'startup'
    INI_path_dirTreeView_root_key = u'dirRoot'
    
    INI_GROUP_Filter = u'Filter'
    INI_filter_deep_key = u'deep'
    
    INI_GROUP_RecentFiles = u'RecentFiles'
    INI_recent_files_sizename = u'size'
    INI_recent_files_key = u'recentFiles'

    INI_GROUP_display = u'Display'
    INI_display_mainWindow = u'mainWindow'
    INI_display_mainWindow_dockwidget = u'dockwidget'
    INI_display_dirTreeView = u'dirTreeView'
    INI_display_bookmarksTreeView = u'bookmarksTreeView'
    
    INI_display_TUPLE_CustomWidgetName = (u'splitter', u'splitterL', u'splitterR', u'headerLeaderTag', u'headerInfo', u'headerTagQuery')

    INI_display_hide_LeaderTagFilter_key = u'leaderTagFilter'
    INI_display_hide_InfoFilter_key = u'infoFilter'
    INI_display_hide_TagQueryFilter_key = u'tagQueryFilter'

    INI_display_expand_InfoTreeView_key = u'expandInfoTreeView'
    INI_display_expand_TagQueryTreeView_key = u'expandTagQueryTreeView'
    
    INI_GROUP_Dir = u'dir'
    

    ## global variable, overrided by settings
    INI_filter_deep =False
    
    INI_recent_files_size = 6
    
    INI_display_hide_LeaderTagFilter = False
    INI_display_hide_InfoFilter = False
    INI_display_hide_TagQueryFilter = False
    
    INI_display_expand_InfoTreeView = False
    INI_display_expand_TagQueryTreeView = True
    
    INI_display_stop_TagQueryModel = False
    
    INI_path_dirTreeView_root = u"c:/program files/Firaxis Games/Sid Meier's Civilization 4/"

    INI_shortcutKey_expand_InfoTreeView = u'Shift+1'
    INI_shortcutKey_collapse_InfoTreeView = u'Shift+2'
    INI_shortcutKey_expand_TagQueryTreeView = u'Shift+3'
    INI_shortcutKey_collapse_TagQueryTreeView = u'Shift+4'
    INI_shortcutKey_switch_LeaderTagFilter = u'Alt+1'
    INI_shortcutKey_switch_InfoFilter = u'Alt+2'
    INI_shortcutKey_switch_TagQueryFilter = u'Alt+3'
    INI_shortcutKey_view_XmlSource = u'Ctrl+U'
    INI_shortcutKey_view_FullScreen = u'F11'
    
    ## global variable, dynamic
    #g_temp_widget
    
    #g_settings
    #g_default_settings
    #g_DICT_settings
    #g_DICT_default_settings
    
    #g_appInfo, g_appDir, g_appDirName, g_appName
    #g_iniFileInfo, g_readmeFileInfo, g_bookmarksFileInfo
    
    #g_XmlDir_Vanilla, g_XmlDir_Wl, g_XmlDir_BtS
    
    ## processing instruction constants
    XML_load_error = 97
    SaveAs_close = 101
    
    ## view source window iId
    WINDOW_help_contents = -123
    
    ## version
    VERSION_debug = False
    VERSION_schema = 0
    VERSION_mainwindow_dockwidget = 1
    VERSION_civ4xml = '0.1.2'
    
    ## text
    TEXT_license = u'''This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.  '''
    
