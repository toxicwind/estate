"""nvidia_swarm_agent.py — Native Llama 3.1 prompt engineering + Grammar-Constrained Decoding."""
from __future__ import annotations
import json, re, logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nvidia_swarm.agent")

LLAMA31_SYSTEM_PREFIX = "<|start_header_id|>system<|end_header_id|>\n\n"
LLAMA31_USER_PREFIX = "<|start_header_id|>user<|end_header_id|>\n\n"
LLAMA31_ASSISTANT_PREFIX = "<|start_header_id|>assistant<|end_header_id|>\n\n"
LLAMA31_STOP = "<|eot_id|>"

@dataclass
class Llama31PromptEngine:
    system_prompt: str = ""
    enable_caching: bool = True
    _cache: Dict[str, str] = field(default_factory=dict, repr=False)

    def render(self, messages: List[Dict[str, str]]) -> str:
        cache_key = json.dumps(messages, sort_keys=True)
        if self.enable_caching and cache_key in self._cache:
            return self._cache[cache_key]
        parts = []
        if self.system_prompt:
            parts.append(f"{LLAMA31_SYSTEM_PREFIX}{self.system_prompt}{LLAMA31_STOP}")
        for msg in messages:
            role, content = msg.get("role", "user"), msg.get("content", "")
            if role == "system" and content != self.system_prompt:
                parts.append(f"{LLAMA31_SYSTEM_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "user":
                parts.append(f"{LLAMA31_USER_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "assistant":
                parts.append(f"{LLAMA31_ASSISTANT_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "tool":
                parts.append(f"{LLAMA31_USER_PREFIX}[TOOL_RESULT]: {content}{LLAMA31_STOP}")
        parts.append(LLAMA31_ASSISTANT_PREFIX)
        result = "".join(parts)
        if self.enable_caching:
            self._cache[cache_key] = result
        return result

    def render_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> str:
        tool_descriptions = []
        for t in tools:
            fn = t.get("function", t)
            name, desc = fn.get("name", "unknown"), fn.get("description", "")
            params = fn.get("parameters", {})
            props, required = params.get("properties", {}), params.get("required", [])
            args = [f"  - {pname} ({pschema.get('type','any')}, {'required' if pname in required else 'optional'}): {pschema.get('description','')}" for pname, pschema in props.items()]
            tool_descriptions.append(f"Tool: {name}\nDescription: {desc}\nArguments:\n" + "\n".join(args))
        tool_block = "\n\n".join(tool_descriptions)
        augmented = f"{self.system_prompt}\n\nYou have access to the following tools. When you need to use a tool, respond with a JSON object containing exactly 'tool' and 'arguments' keys.\n\n{tool_block}\n\nIf no tool is needed, respond normally."
        original = self.system_prompt
        self.system_prompt = augmented
        result = self.render(messages)
        self.system_prompt = original
        return result

@dataclass
class GrammarConstrainedDecoder:
    tool_schemas: List[Dict[str, Any]] = field(default_factory=list)
    max_retries: int = 0
    _compiled_patterns: Dict[str, re.Pattern] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        for t in self.tool_schemas:
            fn = t.get("function", t)
            name = fn.get("name", "")
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            arg_patterns = []
            for pname in sorted(props.keys()):
                ptype = props[pname].get("type", "string")
                val_pat = { "string": r'"[^"]*"', "integer": r"-?\d+", "number": r"-?\d+(?:\.\d+)?",
                            "boolean": r"true|false", "array": r"\[[^\]]*\]" }.get(ptype, r"[^,}]+" )
                arg_patterns.append(rf'"{pname}":\s*{val_pat}')
            args_body = r",\s*".join(arg_patterns) if arg_patterns else ""
            pattern_str = rf'\{{\s*"tool":\s*"{re.escape(name)}"\s*,\s*"arguments":\s*\{{\s*{args_body}\s*\}}\s*\}}'
            try:
                self._compiled_patterns[name] = re.compile(pattern_str, re.VERBOSE)
            except re.error as e:
                logger.warning(f"Failed to compile pattern for {name}: {e}")

    def decode(self, raw_output: str) -> Optional[Dict[str, Any]]:
        for block in re.findall(r"\{[^{}]*\}", raw_output):
            try:
                parsed = json.loads(block)
                if "tool" in parsed and "arguments" in parsed:
                    tool_name = parsed["tool"]
                    if tool_name in self._compiled_patterns and self._compiled_patterns[tool_name].fullmatch(block):
                        return parsed
            except json.JSONDecodeError:
                continue
        return None

    def build_grammar_bnf(self) -> str:
        rules = ["root ::= tool_call | normal_text"]
        tool_alts = []
        for t in self.tool_schemas:
            fn = t.get("function", t)
            name = fn.get("name", "")
            props = fn.get("parameters", {}).get("properties", {})
            arg_rules = []
            for pname in sorted(props.keys()):
                ptype = props[pname].get("type", "string")
                val_rule = { "string": '"[^"]*"', "integer": r"-?\d+", "number": r"-?\d+(?:\.\d+)?",
                             "boolean": r"true|false" }.get(ptype, r"[^,}]+" )
                arg_rules.append(rf'"{pname}":\s*{val_rule}')
            args_str = r",\s*".join(arg_rules) if arg_rules else ""
            tool_alts.append(rf'\{{\s*"tool":\s*"{name}"\s*,\s*"arguments":\s*\{{\s*{args_str}\s*\}}\s*\}}')
        if tool_alts:
            rules.append("tool_call ::= " + " | ".join(tool_alts))
        rules.append(r'normal_text ::= [^\{]+ | "{" [^"\}] "}"')
        return "\n".join(rules)


@dataclass
class TagGrammarConstraint:
    """<tool_call> tag grammar ported from the Drive maximal monolith.

    Some models emit tool calls more reliably as explicit XML-ish tags than as
    JSON blobs. Use grammar_mode="tag" on NvidiaAgent to parse::

        <tool_call>{"tool": "search", "arguments": {"q": "..."}}</tool_call>
    """
    pattern: str = r"<tool_call>(.*?)</tool_call>"

    def extract(self, raw: str) -> Optional[Dict[str, Any]]:
        m = re.search(self.pattern, raw, re.DOTALL)
        if not m:
            return None
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
        if isinstance(obj, dict) and "tool" in obj:
            return {"tool": obj["tool"], "arguments": obj.get("arguments", {})}
        return None

    def wrap(self, tool: str, arguments: Dict[str, Any]) -> str:
        return f"<tool_call>{json.dumps({'tool': tool, 'arguments': arguments})}</tool_call>"


@dataclass
class NvidiaAgent:
    name: str
    system_prompt: str
    model: str = "openai/gpt-oss-20b"  # verified alive-fast 2026-09-14 (old llama-3.1-405b default is dead)
    temperature: float = 0.3
    max_tokens: int = 4096
    tools: List[Dict[str, Any]] = field(default_factory=list)
    handoff_description: Optional[str] = None
    handoff_targets: List[str] = field(default_factory=list)
    enable_grammar: bool = True
    grammar_mode: str = "json"  # "json" (OpenAI tool_calls-ish) or "tag" (<tool_call> tags, Drive merge)
    _prompt_engine: Optional[Llama31PromptEngine] = field(default=None, repr=False)
    _grammar_decoder: Optional[GrammarConstrainedDecoder] = field(default=None, repr=False)

    def __post_init__(self):
        self._prompt_engine = Llama31PromptEngine(system_prompt=self.system_prompt)
        self._grammar_decoder = GrammarConstrainedDecoder(tool_schemas=self.tools) if self.enable_grammar and self.tools else GrammarConstrainedDecoder(tool_schemas=[])

    def prepare_messages(self, messages: List[Dict[str, str]]) -> str:
        return self._prompt_engine.render_with_tools(messages, self.tools) if self.tools else self._prompt_engine.render(messages)

    def parse_response(self, raw_output: str) -> Dict[str, Any]:
        if self.tools:
            tool_call = None
            if self.grammar_mode == "tag":
                tool_call = TagGrammarConstraint().extract(raw_output)
            elif self._grammar_decoder:
                tool_call = self._grammar_decoder.decode(raw_output)
            if tool_call:
                return {"role": "assistant", "content": None, "tool_calls": [{"id": f"call_{hash(tool_call['tool']) & 0xFFFFFFFF:08x}", "type": "function", "function": {"name": tool_call["tool"], "arguments": json.dumps(tool_call["arguments"])}}]}
        return {"role": "assistant", "content": raw_output}

    def get_grammar_bnf(self) -> Optional[str]:
        return self._grammar_decoder.build_grammar_bnf() if self._grammar_decoder else None

    def to_core_node(self, agent_id: str) -> "AgentNode":
        from .nvidia_swarm_core import AgentNode
        return AgentNode(agent_id=agent_id, name=self.name, system_prompt=self.system_prompt, tools=self.tools,
                         model=self.model, temperature=self.temperature, max_tokens=self.max_tokens, handoff_targets=self.handoff_targets)
