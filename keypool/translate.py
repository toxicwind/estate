"""Wire translation: OpenAI chat-completions <-> Gemini EAP Interactions API.

Implements the official Gemini Tool Retrieval (EAP) protocol:
- Server-side tool retrieval with {"type": "tool_search"} and defer_loading: true
- Unwraps OpenAI tool format (tools[].function) to Interactions format
- Translates tool results into EAP {"type": "function_result"} inputs
- Translates EAP steps with {"type": "function_call"} into OpenAI tool_calls
"""

import json
from typing import Any, Dict, List, Optional


def openai_to_interactions(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return doc

    # If already native interactions format, pass through
    if "input" in doc and "messages" not in doc:
        return doc

    messages = doc.get("messages") or []
    out: Dict[str, Any] = {"model": doc.get("model")}

    # 1. Translate tools to Gemini EAP format
    openai_tools = doc.get("tools")
    if openai_tools and isinstance(openai_tools, list):
        eap_tools: List[dict] = [{"type": "tool_search"}]
        has_functions = False
        for t in openai_tools:
            if not isinstance(t, dict):
                continue
            ttype = t.get("type")
            if ttype == "function":
                fn = t.get("function", {})
                if not isinstance(fn, dict):
                    fn = {}
                name = fn.get("name") or t.get("name", "")
                desc = fn.get("description") or t.get("description", "")
                params = fn.get("parameters") or t.get("parameters", {"type": "object", "properties": {}})
                eap_tools.append({
                    "type": "function",
                    "name": name,
                    "description": desc,
                    "defer_loading": True,
                    "parameters": params
                })
                has_functions = True
            elif ttype in ("tool_search", "mcp_server"):
                eap_tools.append(t)
        if has_functions or len(eap_tools) > 1:
            out["tools"] = eap_tools

    # 2. Check if the latest message(s) are tool responses (Turn 2+ of tool execution)
    tool_results = []
    for m in messages:
        if isinstance(m, dict) and m.get("role") == "tool":
            call_id = m.get("tool_call_id") or m.get("id") or ""
            name = m.get("name") or ""
            raw_content = m.get("content", "")
            try:
                res_data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
            except Exception:
                res_data = {"content": raw_content}
            tool_results.append({
                "type": "function_result",
                "name": name,
                "call_id": call_id,
                "result": res_data
            })

    if tool_results:
        # Client-side / server-side function result submission
        out["input"] = tool_results
    else:
        # Standard conversational input
        parts = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "user")
            c = m.get("content", "")
            if isinstance(c, list):
                c = "".join(p.get("text", "") for p in c if isinstance(p, dict))
            parts.append(f"{role}: {c}")
        out["input"] = "\n".join(parts)

    for k in ("previous_interaction_id", "stream"):
        if k in doc:
            out[k] = doc[k]

    return out


def interactions_to_openai(doc: dict, model: str) -> dict:
    if not isinstance(doc, dict):
        return doc

    steps = doc.get("steps") or []
    tool_calls: List[dict] = []
    text_chunks: List[str] = []

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        stype = step.get("type")

        # Function calls issued by model
        if stype == "function_call":
            call_id = step.get("id") or f"call_eap_{idx}_{step.get('name', 'fn')}"
            name = step.get("name") or ""
            args = step.get("arguments") or {}
            args_str = json.dumps(args) if isinstance(args, dict) else str(args)
            tool_calls.append({
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": args_str
                }
            })
        elif stype == "mcp_server_tool_call":
            call_id = step.get("id") or f"mcp_eap_{idx}"
            server = step.get("server_name", "mcp")
            tname = step.get("name", "")
            full_name = f"{server}:{tname}" if server else tname
            args = step.get("arguments") or {}
            args_str = json.dumps(args) if isinstance(args, dict) else str(args)
            tool_calls.append({
                "id": call_id,
                "type": "function",
                "function": {
                    "name": full_name,
                    "arguments": args_str
                }
            })
        elif stype in ("message", "model_output", "text", "output_text"):
            c = step.get("content")
            if isinstance(c, str):
                text_chunks.append(c)
            elif isinstance(c, list):
                text_chunks.extend(x.get("text", "") for x in c if isinstance(x, dict) and isinstance(x.get("text"), str))

    # Determine finish_reason and message structure
    if tool_calls:
        finish_reason = "tool_calls"
        message_obj: Dict[str, Any] = {
            "role": "assistant",
            "content": "".join(text_chunks) if text_chunks else None,
            "tool_calls": tool_calls
        }
    else:
        finish_reason = "stop"
        content_text = "".join(text_chunks)
        if not content_text:
            # Fallback if no recognizable steps but output exists
            content_text = doc.get("output", "") or ""
            if not content_text and "error" in doc:
                content_text = json.dumps(doc["error"])
        message_obj = {
            "role": "assistant",
            "content": content_text
        }

    return {
        "id": doc.get("id", "eap_interaction"),
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": message_obj,
            "finish_reason": finish_reason
        }],
        "usage": doc.get("usage") or {},
        "_eap_status": doc.get("status"),
        "_eap_steps": [s.get("type") for s in steps if isinstance(s, dict)]
    }
