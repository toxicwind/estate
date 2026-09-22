import json, os, urllib.request, urllib.parse

H = {
    "Authorization": "Bearer " + os.environ["GH_TOKEN"],
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def gh(url):
    req = urllib.request.Request(url, headers=H)
    return json.load(urllib.request.urlopen(req, timeout=30))

queries = {
    "stealth-args": "disable-blink-features AutomationControlled playwright",
    "webdriver-init": "navigator.webdriver addInitScript playwright",
    "ignoredefaultargs": "ignoreDefaultArgs browserless launch",
    "secure-browser-issue": "This browser or app may not be secure playwright",
}

for name, q in queries.items():
    print("=" * 20, name)
    endpoint = "/search/issues" if name == "secure-browser-issue" else "/search/code"
    url = "https://api.github.com" + endpoint + "?q=" + urllib.parse.quote(q) + "&per_page=5"
    try:
        d = gh(url)
        for it in d.get("items", []):
            repo = (it.get("repository") or {}).get("full_name", "?")
            print(repo, "|", it.get("path", it.get("title", "?")), "|", it.get("html_url"))
    except Exception as e:
        print("ERR", e)
