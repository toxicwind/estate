import json,sys
d=json.load(open(sys.argv[1]))
for s in d["strategies"]:
    print("{name}\t{cmd}\t{match}\t{suite}".format(**s))
