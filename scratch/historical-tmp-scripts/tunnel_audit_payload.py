import subprocess, re, json

def sh(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)
        return (r.stdout.strip() or "(empty)")[:1500]
    except Exception as e:
        return "ERR: %s" % e

out = {}
out["listener"] = sh("ss -tlnp 2>/dev/null | grep ':25379' || echo NO_LISTENER_25379")
try:
    txt = open("/home/toxic/sovereign/pitchfork.toml").read()
    m = re.search(r"\[daemons\.ws-exec-tunnel\].*?(?=\n\[|\Z)", txt, re.S)
    out["toml_section"] = (m.group(0).strip() if m else "SECTION_NOT_FOUND")[:800]
except Exception as e:
    out["toml_section"] = "ERR %s" % e
out["refs_25379"] = sh("grep -rn '25379' /home/toxic/sovereign/pitchfork.toml /home/toxic/sovereign/config/ports.env 2>/dev/null | head -8")
out["git_history"] = sh("cd /home/toxic/sovereign && git log --oneline -8 -S 'ws-exec-tunnel' -- pitchfork.toml")
out["pitchfork_state"] = sh("cd /home/toxic/sovereign && pitchfork list 2>/dev/null | grep -i 'ws-exec-tunnel' || echo NOT_IN_PITCHFORK_LIST")

has_listener = "NO_LISTENER_25379" not in out["listener"]
in_toml = "SECTION_NOT_FOUND" not in out["toml_section"] and "ERR" not in out["toml_section"]
if has_listener:
    verdict = "REQUIRED_INFRA: something is live on :25379"
elif in_toml and "NOT_IN_PITCHFORK" not in out["pitchfork_state"]:
    verdict = "REGISTERED_BUT_DOWN: in pitchfork.toml, not listening — needs restart or is failing"
elif in_toml:
    verdict = "STALE: in pitchfork.toml but not registered/running — candidate for removal"
else:
    verdict = "MISDOCUMENTED_OR_GONE: no toml section, no listener"
out["verdict"] = verdict
print(json.dumps(out, indent=1))
print("TUNNEL_AUDIT_DONE")
