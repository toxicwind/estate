# -*- coding: utf-8 -*-
from eternalmgr.modules.control import addonPath, addonVersion, joinPath
from eternalmgr.windows.textviewer import TextViewerXML

def get(file):
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	helpFile = joinPath(eternalmgr_path, 'lib', 'eternalmgr', 'help', file + '.txt')
	r = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite -  v%s - %s[/B]' % (eternalmgr_version, file)
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows

def get_login():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	helpFile = joinPath(eternalmgr_path, 'lib', 'eternalmgr', 'help', 'login.txt')
	r = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite -  v%s - Torbox & OffCloud Auth Help[/B]' % (eternalmgr_version)
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
	
def get_restore():
	eternalmgr_path = addonPath()
	eternalmgr_version = addonVersion()
	helpFile = joinPath(eternalmgr_path, 'lib', 'eternalmgr', 'help', 'restore.txt')
	r = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]AM Lite -  v%s - Restore to Default[/B]' % (eternalmgr_version)
	windows = TextViewerXML('textviewer.xml', eternalmgr_path, heading=heading, text=text)
	windows.run()
	del windows
