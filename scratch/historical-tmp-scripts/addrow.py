l = open('/home/toxic/sovereign/docs/fleet-knowledgebase.md').readlines()
row = '| browserless-mcp-audit | Browserless MCP 1.3.0 audit: 4 integration bugs fixed | browserless-audit-crew | DONE 2026-09-21 commit c1c544eb1f |\n'
l.insert(187, row)
open('/home/toxic/sovereign/docs/fleet-knowledgebase.md','w').writelines(l)
print('added')
