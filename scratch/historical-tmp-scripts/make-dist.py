import json, collections

src = "projects/mesh/gateway/mcp_config.json"
dst = "projects/mesh/gateway/mcp_config.json.dist"

cfg = json.load(open(src))

scrubbed = []


def scrub_env(obj):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            v = obj[k]
            if k == "api_key" and isinstance(v, str):
                obj[k] = "REDACTED-use-MCPPROXY_API_KEY-env"
                scrubbed.append("api_key")
            elif k == "env" and isinstance(v, dict):
                for ek in list(v.keys()):
                    if ek in ("SCOUT_API_KEY", "PROMETHEUS_URL", "SCOUT_BASE_URL"):
                        v[ek] = "REDACTED-use-" + ek + "-env"
                        scrubbed.append("env/" + ek)
            else:
                scrub_env(v)
    elif isinstance(obj, list):
        for v in obj:
            scrub_env(v)


scrub_env(cfg)

with open(dst, "w") as f:
    json.dump(cfg, f, indent=2, sort_keys=True)
    f.write("\n")

print("scrubbed fields:", scrubbed)
print("dist written:", dst)
