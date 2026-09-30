import re

HERD = "/home/toxic/sovereign/projects/herd"

# server.go: remove embedded UI routes
p = HERD + "/internal/server/server.go"
s = open(p).read()
old = '\t// Embedded UI.\n\tmux.Handle("GET /ui/", chain.New(authMW).ThenFunc(s.handleUI))\n\tmux.HandleFunc("GET /favicon.ico", s.handleFavicon)\n\n'
assert old in s, "server.go UI block not found"
s = s.replace(old, "")
open(p, "w").write(s)
print("server.go: UI routes removed")

# api.go: redirects pointed at /ui; point at ranch dashboard
p = HERD + "/internal/server/api.go"
s = open(p).read()
n1 = s.count('"/ui"')
n2 = s.count('"/ui/models"')
s = s.replace('"/ui/models"', '"https://github.com/toxicwind/ranch/tree/main/ui"')
s = s.replace('"/ui"', '"https://github.com/toxicwind/ranch/tree/main/ui"')
open(p, "w").write(s)
print("api.go: redirects repointed (%d + %d)" % (n1, n2))

# log.go: HTML clients went to /ui/; drop that branch
p = HERD + "/internal/server/log.go"
s = open(p).read()
old = '\tif strings.Contains(r.Header.Get("Accept"), "text/html") {\n\t\thttp.Redirect(w, r, "/ui/", http.StatusFound)\n\t\treturn\n\t}\n'
assert old in s, "log.go HTML branch not found"
s = s.replace(old, "")
open(p, "w").write(s)
print("log.go: HTML->UI branch removed")
