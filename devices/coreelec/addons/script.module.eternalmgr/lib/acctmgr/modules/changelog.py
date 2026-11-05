# -*- coding: utf-8 -*-
import xbmcvfs
from eternalmgr.modules.control import addonPath, addonVersion, joinPath, translatePath
from eternalmgr.windows.textviewer import TextViewerXML

supported_path = translatePath('special://home/addons/script.module.eternalmgr/resources/skins/Default/media/common/')

def get_changelog():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(eternalmgr_path, 'changelog.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite -  v%s - ChangeLog[/B]' % eternalmgr_version
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_trakt():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_trakt.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_mdblist():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_mdblist.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
	
def get_supported_debrid():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_debrid.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_torbox():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_torbox.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
	
def get_supported_easydebrid():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_easydebrid.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
	
def get_supported_offcloud():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_offcloud.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_easynews():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_easynews.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
	
def get_supported_ext():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_ext.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_maxql():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_maxql.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_supported_autoplay():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	changelogfile = joinPath(supported_path, 'supported_autoplay.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite - Supported Add-ons[/B]'
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
