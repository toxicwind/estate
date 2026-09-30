import re

HERD = "/home/toxic/sovereign/projects/herd"

# api_test.go: redirects now point at the ranch dashboard
p = HERD + "/internal/server/api_test.go"
s = open(p).read()
old = 'for path, want := range map[string]string{"/": "/ui", "/upstream": "/ui/models"} {'
new = ('ranchUI := "https://github.com/toxicwind/ranch/tree/main/ui"\n'
       '\tfor path, want := range map[string]string{"/": ranchUI, "/upstream": ranchUI} {')
assert old in s, "redirect test not found"
s = s.replace(old, new)
open(p, "w").write(s)
print("api_test.go: redirect expectations updated")

# log_test.go: the HTML->/ui/ redirect test is dead; remove it
p = HERD + "/internal/server/log_test.go"
s = open(p).read()
start = s.find("func TestServer_HandleLogs_HTMLRedirect")
assert start > 0, "log redirect test not found"
m = re.search(r"\nfunc ", s[start + 10:])
end = start + 10 + m.start() + 1 if m else len(s)
s = s[:start] + s[end:]
open(p, "w").write(s)
print("log_test.go: stale HTML redirect test removed")
