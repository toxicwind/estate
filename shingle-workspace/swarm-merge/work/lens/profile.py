#!/usr/bin/env python3
"""
Lens Profile System — Maps each swarm agent to its NVIDIA-optimized configuration.
Integrates swarm directly into lens with nv (NVIDIA NIM) support.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class LensProfile:
    """A lens profile defines how a specific agent type maps to NVIDIA NIM capabilities.

    Each profile specifies:
    - Model selection (405B for reasoning, 70B for speed, 8B for simple tasks)
    - Prompt engineering strategy (native Llama 3.1 format)
    - Tool schema (grammar-constrained JSON)
    - KV-cache strategy (context window packing)
    - Concurrency level (how many parallel instances)
    """

    name: str
    agent_type: str  # "researcher", "coder", "analyst", "orchestrator", etc.
    model: str = "openai/gpt-oss-20b"
    temperature: float = 0.3
    max_tokens: int = 4096
    system_prompt: str = ""
    tools: List[Dict] = field(default_factory=list)
    grammar: str = ""
    max_concurrent: int = 4
    kv_cache_strategy: str = "full"  # "full", "sliding", "sink"

    def to_agent_config(self) -> Dict[str, Any]:
        """Convert lens profile to NvidiaAgent constructor args."""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "grammar": self.grammar,
        }

# === PRE-BUILT LENS PROFILES ===

RESEARCHER_LENS = LensProfile(
    name="nvidia_researcher",
    agent_type="researcher",
    model="openai/gpt-oss-20b",
    temperature=0.2,
    max_tokens=8192,
    max_concurrent=8,
    kv_cache_strategy="sliding",
    system_prompt="""You are a research agent optimized for NVIDIA NIM inference.
Your task is to search, analyze, and synthesize information from multiple sources.
You have access to web_search, web_open_url, and data analysis tools.
Be thorough but concise. Always cite sources.

When using tools, respond with JSON: {"tool": "TOOL_NAME", "params": {"query": "..."}}""",
    tools=[
        {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "web_open_url",
            "description": "Open a URL and read its content",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"},
                },
                "required": ["url"],
            },
        },
    ],
)

CODER_LENS = LensProfile(
    name="nvidia_coder",
    agent_type="coder",
    model="openai/gpt-oss-20b",
    temperature=0.1,
    max_tokens=16384,
    max_concurrent=4,
    kv_cache_strategy="full",
    system_prompt="""You are a code generation agent running on NVIDIA NIM.
Your task is to write, review, and debug Python code.
You have access to ipython execution and file operations.
Always write clean, documented code. Use type hints.

When using tools, respond with JSON: {"tool": "TOOL_NAME", "params": {"code": "..."}}""",
    tools=[
        {
            "name": "ipython",
            "description": "Execute Python code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                },
                "required": ["code"],
            },
        },
        {
            "name": "write_file",
            "description": "Write a file to disk",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        },
    ],
)

ANALYST_LENS = LensProfile(
    name="nvidia_analyst",
    agent_type="analyst",
    model="meta/llama-3.1-70b-instruct",  # 70B is faster for analysis
    temperature=0.0,
    max_tokens=4096,
    max_concurrent=12,
    kv_cache_strategy="sink",
    system_prompt="""You are a data analysis agent on NVIDIA NIM.
Your task is to analyze datasets, generate charts, and extract insights.
You have access to data sources and visualization tools.
Be precise with numbers. Show your work.

When using tools, respond with JSON: {"tool": "TOOL_NAME", "params": {"data_source": "..."}}""",
    tools=[
        {
            "name": "get_data_source",
            "description": "Query a data source",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Data source name"},
                    "api": {"type": "string", "description": "API name"},
                    "params": {"type": "object", "description": "Query parameters"},
                },
                "required": ["source", "api"],
            },
        },
    ],
)

ORCHESTRATOR_LENS = LensProfile(
    name="nvidia_orchestrator",
    agent_type="orchestrator",
    model="openai/gpt-oss-20b",
    temperature=0.4,
    max_tokens=4096,
    max_concurrent=2,
    kv_cache_strategy="full",
    system_prompt="""You are the swarm orchestrator running on NVIDIA NIM.
Your task is to coordinate multiple agents, manage the DAG execution,
and ensure optimal throughput across the GPU cluster.
You have access to agent spawning and monitoring tools.
Make decisions about parallelization and resource allocation.

When using tools, respond with JSON: {"tool": "TOOL_NAME", "params": {"agent_name": "..."}}""",
    tools=[
        {
            "name": "spawn_agent",
            "description": "Spawn a new agent instance",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "Name of agent to spawn"},
                    "lens_profile": {"type": "string", "description": "Lens profile to use"},
                },
                "required": ["agent_name", "lens_profile"],
            },
        },
        {
            "name": "monitor_agents",
            "description": "Get status of all running agents",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    ],
)

# Registry of all lens profiles
LENS_REGISTRY: Dict[str, LensProfile] = {
    "researcher": RESEARCHER_LENS,
    "coder": CODER_LENS,
    "analyst": ANALYST_LENS,
    "orchestrator": ORCHESTRATOR_LENS,
}

def get_lens(profile_name: str) -> LensProfile:
    """Get a lens profile by name."""
    return LENS_REGISTRY.get(profile_name, RESEARCHER_LENS)

def list_lenses() -> List[str]:
    """List all available lens profiles."""
    return list(LENS_REGISTRY.keys())

def create_swarm_dag(task: str, lens_names: List[str]) -> List[Dict]:
    """Create a DAG configuration for a multi-agent swarm task.

    Example:
        create_swarm_dag("Analyze IPTV repos", ["researcher", "analyst", "coder"])
    """
    dag = []
    for i, lens_name in enumerate(lens_names):
        lens = get_lens(lens_name)
        dag.append({
            "agent_name": lens.name,
            "dependencies": [lens_names[j] for j in range(i)] if i > 0 else [],
            "inputs": {"task": task, "step": i + 1},
            "output_key": f"{lens_name}_result",
        })
    return dag
