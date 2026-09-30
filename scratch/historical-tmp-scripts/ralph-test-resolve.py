import importlib.util
spec = importlib.util.spec_from_file_location("bt", "/tmp/ralph-bidder-test.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print("import ok")
    m = mod._resolve_ralph_model("http://127.0.0.1:25100/v1", timeout=20)
    print("resolved model:", m)
except Exception as e:
    import traceback
    traceback.print_exc()
