"""Expand compact sig dialect to JSON Schema.

Dialect (from gatehouse results):
  (owner*:str, repo*:str, page:num)
  - *           required
  - ~           lossy (schema collapsed)
  - (~)         schema unavailable
  - =default    default value
  - :enum[a|b]  enumerated values
  - [str]       array of str
"""
import re

_PARAM = re.compile(r"([a-z_][a-z0-9_]*)([*~]*):([^=,)]+)(?:=([^,)]+))?", re.I)

_TYPE_MAP = {
    "str":"string","string":"string","num":"number","number":"number",
    "int":"integer","integer":"integer","bool":"boolean","boolean":"boolean",
    "obj":"object","object":"object","any":"object",
}

def expand(sig: str) -> dict:
    """Return JSON Schema for a compact signature."""
    if not sig or sig.strip() in ("()","(~)"):
        return {"type":"object","properties":{}}
    body = sig.strip().strip("()")
    props, required = {}, []
    for m in _PARAM.finditer(body):
        name, marks, typ, default = m.groups()
        if "~" in marks:
            js = {"type":"object","description":"[lossy — call describe_tool]"}
        elif typ.startswith("enum["):
            vals = typ[5:-1].split("|")
            js = {"type":"string","enum":vals}
        elif typ.startswith("[") and typ.endswith("]"):
            inner = _TYPE_MAP.get(typ[1:-1].lower(),"object")
            js = {"type":"array","items":{"type":inner}}
        else:
            js = {"type": _TYPE_MAP.get(typ.lower(),"object")}
        if default is not None:
            js["default"] = default
        props[name] = js
        if "*" in marks: required.append(name)
    out = {"type":"object","properties":props}
    if required: out["required"] = required
    return out
