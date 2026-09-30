import re
t = open("/home/toxic/.browserless/.env").read()
m = re.search(r"BROWSERLESS_TOKEN\s*=\s*[\"']?([^\"'\n]+)", t)
print(m.group(1).strip().strip("\"'"))
