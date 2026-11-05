"""
	EternalScrapers Module
"""

from eternalscrapers.modules.control import addonPath, addonVersion, joinPath
from eternalscrapers.modules.textviewer import TextViewerXML


def get():
	eternalscrapers_path = addonPath()
	eternalscrapers_version = addonVersion()
	changelogfile = joinPath(eternalscrapers_path, 'changelog.txt')
	r = open(changelogfile, 'r', encoding='utf-8', errors='ignore')
	text = r.read()
	r.close()
	heading = '[B]eternalscrapers -  v%s - ChangeLog[/B]' % eternalscrapers_version
	windows = TextViewerXML('textviewer.xml', eternalscrapers_path, heading=heading, text=text)
	windows.run()
	del windows
