"""Wire translation: OpenAI chat-completions <-> Gemini Interactions."""

import json


def openai_to_interactions(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return doc
    if "input" in doc and "messages" not in doc:
        return doc
    parts = []
    for m in doc.get("messages") or []:
        if not isinstance(m, dict):
            continue
        c = m.get("content", "")
        if isinstance(c, list):
            c = "".join(p.get("text", "") for p in c if isinstance(p, dict))
        parts.append(f"{m.get('role', 'user')}: {c}")
    out = {"model": doc.get("model"), "input": "\n".join(parts)}
    for k in ("tools", "previous_interaction_id"):
        if k in doc:
            out[k] = doc[k]
    return out


def interactions_to_openai(doc: dict, model: str) -> dict:
    if not isinstance(doc, dict):
        return doc
    text = None
    for step in reversed(doc.get("steps") or []):
        if not isinstance(step, dict):
            continue
        if step.get("type") in ("message", "model_output", "text", "output_text"):
            c = step.get("content")
            if isinstance(c, str):
                text = c
                break
            if isinstance(c, list):
                chunks = [x.get("text", "") for x in c
                          if isinstance(x, dict) and isinstance(x.get("text"), str)]
                if chunks:
                    text = "".join(chunks)
                    break
    if text is None:
        text = json.dumps(doc)
    return {
        "id": doc.get("id", "eap"),
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0,
                     "message": {"role": "assistant", "content": text},
                     "finish_reason": "stop"}],
        "usage": doc.get("usage") or {},
        "_eap_status": doc.get("status"),
        "_eap_steps": [s.get("type") for s in (doc.get("steps") or [])
                       if isinstance(s, dict)],
    }
