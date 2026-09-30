def buildsrv_metrics(out):
    # Added 2026-09-21: buildsrv (fleet build server, :25148) health + load.
    up = 0
    try:
        req = urllib.request.Request("http://127.0.0.1:25148/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status == 200:
                body = json.loads(r.read(65536).decode("utf-8", "replace") or "{}")
                up = 1 if body.get("ok") is True else 0
    except Exception:
        pass
    out.append("sovereign_buildsrv_up %d" % up)
    for metric, sub in (("sovereign_buildsrv_queue_depth", "queue"),
                        ("sovereign_buildsrv_active_jobs", "active")):
        n = 0
        try:
            d = os.path.join("/home/toxic/buildsrv", sub)
            n = sum(1 for f in os.listdir(d) if f.endswith(".json"))
        except OSError:
            pass
        out.append("%s %d" % (metric, n))


