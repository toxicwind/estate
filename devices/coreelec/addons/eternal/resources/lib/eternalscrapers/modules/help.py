"""
	EternalScrapers Module
"""

from eternalscrapers.modules.control import addonPath, addonVersion, joinPath
from eternalscrapers.modules.textviewer import TextViewerXML


def get(file):
	eternalscrapers_path = addonPath()
	eternalscrapers_version = addonVersion()
	helpFile = joinPath(eternalscrapers_path, 'resources', 'help', file + '.txt')
	r = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]eternalscrapers -  v%s - %s[/B]' % (eternalscrapers_version, file)
	windows = TextViewerXML('textviewer.xml', eternalscrapers_path, heading=heading, text=text)
	windows.run()
	del windows
