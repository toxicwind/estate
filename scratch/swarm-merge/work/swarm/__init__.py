"""NVIDIA-NIM-Swarm Merger — core + optional integrations.

Core (stdlib-only at import): always available.
Integrations (zmq, proxy, mcp, git, unshare, envd): imported tolerantly —
missing third-party deps degrade to None instead of breaking `import swarm`.
"""
__version__ = "0.3.0-maximal"

from .nvidia_swarm_core import NvidiaSwarm, SwarmDAG, AgentNode
from .nvidia_swarm_agent import (
    NvidiaAgent, Llama31PromptEngine, GrammarConstrainedDecoder,
    TagGrammarConstraint,
)
from .nvidia_swarm_transport import TritonTransport, NvidiaNIMClient, PersistentConnectionPool
from .nvidia_swarm_archivefs import ArchiveFS, ArchiveFSEntry
from .transport_profiles import TransportProfile, TRANSPORT_PROFILES, get_transport_profile


def _try_import(module: str, names):
    try:
        mod = __import__(f"swarm.{module}", fromlist=names)
        return {n: getattr(mod, n) for n in names}
    except Exception:
        return {n: None for n in names}


_opt = {}
_opt.update(_try_import("nvidia_swarm_zmq", ["ZMQEngine", "ZMQTool", "ZMQExecutionResult"]))
_opt.update(_try_import("nvidia_swarm_proxy", ["DaemonTunnel", "SquidProxy", "FlareSolverrGateway", "ProxyStack"]))
_opt.update(_try_import("nvidia_swarm_mcp", ["MCPManager", "MCPServer", "MCP_REGISTRY"]))
_opt.update(_try_import("nvidia_swarm_git", ["GitPushHelper"]))
_opt.update(_try_import("nvidia_swarm_unshare", ["UnshareRoot"]))
_opt.update(_try_import("nvidia_swarm_envd", ["EnvdMimicry"]))
globals().update(_opt)

__all__ = [
    "NvidiaSwarm", "SwarmDAG", "AgentNode",
    "NvidiaAgent", "Llama31PromptEngine", "GrammarConstrainedDecoder",
    "TagGrammarConstraint",
    "TritonTransport", "NvidiaNIMClient", "PersistentConnectionPool",
    "ArchiveFS", "ArchiveFSEntry",
    "TransportProfile", "TRANSPORT_PROFILES", "get_transport_profile",
] + [k for k, v in _opt.items() if v is not None]
