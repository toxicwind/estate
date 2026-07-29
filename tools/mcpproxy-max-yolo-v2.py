#!/usr/bin/env python3
"""Upgrade ~/.mcpproxy/mcp_config.json to a corrected max-yolo config based on source-code audit."""
import json
import os
import shutil
from datetime import datetime, timezone

CONFIG_PATH = "/home/toxic/.mcpproxy/mcp_config.json"

with open(CONFIG_PATH, "r") as f:
    cfg = json.load(f)

# Remove non-canonical keys that code ignores / rejects
cfg.pop("_max_yolo_applied_at", None)
cfg.pop("reconnect_on_use", None)  # per-server only, not global

# ---- Network / core ---------------------------------------------------------
cfg["listen"] = "0.0.0.0:25109"
cfg["require_mcp_auth"] = False

# ---- Discovery / limits ------------------------------------------------------
cfg["tools_limit"] = 100
cfg["tool_response_limit"] = 100000
cfg["max_result_size_chars"] = 1000000
cfg["call_tool_timeout"] = "5m0s"
cfg["init_timeout"] = "120s"
cfg["health_check_interval"] = "15s"
cfg["tool_discovery_interval"] = "2m"

# ---- Token-efficient tool exposure -----------------------------------------
cfg["tool_response_mode"] = "compact"
cfg["toon_output"] = "adaptive"
cfg["toon_min_savings_pct"] = 5

# ---- Code execution ---------------------------------------------------------
cfg["enable_code_execution"] = True
cfg["code_execution_timeout_ms"] = 600000
cfg["code_execution_max_tool_calls"] = 100
cfg["code_execution_pool_size"] = 30

# ---- Management gates (keep writable but allow everything) ------------------
cfg["allow_server_add"] = True
cfg["allow_server_remove"] = True
cfg["disable_management"] = False
cfg["read_only_mode"] = False

# ---- Quarantine / security (in-process baseline only; no Docker) -----------
cfg["quarantine_enabled"] = True
cfg["security"] = {
    "scan_timeout_default": "60s",
    "integrity_check_interval": "1h",
    "integrity_check_on_restart": True,
    "scanner_registry_url": "",
    "deep_scan": {
        "enabled": False,
        "fetch_package_source": False,
        "disable_no_new_privileges": False,
        "scanners": []
    }
}

# ---- Sensitive data detection -----------------------------------------------
cfg["sensitive_data_detection"] = {
    "enabled": True,
    "scan_requests": True,
    "scan_responses": True,
    "max_payload_size_kb": 8192,
    "entropy_threshold": 3.5,
    "categories": {
        "api_token": True,
        "auth_token": True,
        "cloud_credentials": True,
        "credit_card": True,
        "database_credential": True,
        "high_entropy": True,
        "private_key": True,
        "sensitive_file": True
    },
    "sensitive_keywords": [
        "nvapi-", "mcp_agt_", "ghp_", "github_pat_", "sk-", "sk-ant-", "xoxb-", "xoxp-",
        "AKIA", "ASIA", "AIza", "ya29.", "1//0", "r8_", "p8_", "lp_", "lv_"
    ],
    "custom_patterns": [
        {
            "name": "nvidia-nim-key",
            "regex": "nvapi-[A-Za-z0-9_-]{40,}",
            "severity": "critical",
            "category": "api_token"
        },
        {
            "name": "mcp-agent-token",
            "regex": "mcp_agt_[A-Za-z0-9_-]{32,}",
            "severity": "critical",
            "category": "api_token"
        }
    ]
}

# ---- Output sanitisation ----------------------------------------------------
cfg["output_sanitisation"] = {
    "spotlight_untrusted": True,
    "response_action": "spotlight",
    "strip_control_chars": True,
    "strip_classes": ["ansi", "c0c1", "bidi", "zero_width"],
    "max_redactions": 500
}

# ---- Output validation ------------------------------------------------------
cfg["output_validation"] = {
    "mode": "strict",
    "max_bytes": 20971520,
    "max_depth": 256,
    "missing_structured_content": "warn"
}

# ---- Environment / proxy ----------------------------------------------------
cfg["check_server_repo"] = True
cfg["forward_proxy_env"] = True
cfg.setdefault("environment", {})
cfg["environment"]["inherit_system_safe"] = True
cfg["environment"]["enhance_path"] = True

# ---- Logging ----------------------------------------------------------------
cfg["logging"] = {
    "level": "info",
    "enable_file": True,
    "enable_console": True,
    "filename": "main.log",
    "max_size": 100,
    "max_backups": 20,
    "max_age": 90,
    "compress": True,
    "json_format": True
}

# ---- Observability ----------------------------------------------------------
cfg["observability"] = {
    "usage_cache_ttl": "1s",
    "usage_persist_interval": "5s",
    "metrics": {"enabled": True},
    "tracing": {
        "enabled": True,
        "protocol": "http",
        "endpoint": "localhost:4318",
        "sample_rate": 0.8
    }
}

# ---- Update checks ----------------------------------------------------------
cfg["update_check"] = {"enabled": True, "channel": "stable"}

# ---- Health / risk warnings -------------------------------------------------
cfg["tool_response_session_risk_warning"] = False  # save tokens; structured fields still present
cfg["oauth_expiry_warning_hours"] = 4.0

# ---- Intent declaration -----------------------------------------------------
cfg["intent_declaration"] = {"strict_server_validation": True}

# ---- TLS (still off by default; user flips via env when needed) -------------
cfg["tls"] = {"enabled": False, "require_client_cert": False, "hsts": True}

# ---- Tokenizer --------------------------------------------------------------
cfg["tokenizer"] = {"enabled": True, "default_model": "gpt-4o", "encoding": "o200k_base"}

# ---- Docker isolation: explicitly OFF per user request ----------------------
cfg["docker_isolation"] = {"enabled": False, "mode": "none"}
cfg["docker_recovery"] = {"enabled": False}

# ---- Custom instructions for agents -----------------------------------------
cfg["instructions"] = (
    "You are talking to MCPProxy, a smart MCP proxy. "
    "Use retrieve_tools to search for tools before assuming a capability is missing. "
    "Use describe_tool to fetch full schemas for compact results. "
    "Use call_tool_read / call_tool_write / call_tool_destructive with intent to execute. "
    "Tool names are in the form serverName:toolName."
)

# ---- Ensure every server has sensible yolo defaults -------------------------
LOCAL_PATH_HINTS = (
    "/home/toxic/", "/home/toxic/.cargo/bin/", "/home/toxic/.local/bin/",
    "/home/toxic/.bun/bin/", "/home/toxic/mcp-installs/", "/home/toxic/mcp-filesystem/",
    "/home/toxic/projects/", "system-monitor"
)
for s in cfg.get("mcpServers", []):
    s.setdefault("enabled", True)
    s.setdefault("quarantined", False)
    cmd = s.get("command", "")
    args = " ".join(s.get("args", []))
    is_local = any(h in cmd or h in args for h in LOCAL_PATH_HINTS)
    # Use trust_mode (spec 086) which supersedes auto_approve_tool_changes
    if is_local:
        s["trust_mode"] = "auto"
        s.setdefault("auto_approve_tool_changes", True)
    else:
        s.setdefault("trust_mode", "scan")
    # Explicitly disable isolation per user request (no Docker)
    s.setdefault("isolation", {})["mode"] = "none"
    s["isolation"]["enabled"] = False
    # Shorten discovery for active servers
    s.setdefault("health_check_interval", "15s")
    s.setdefault("tool_discovery_interval", "2m")

# ---- Add a few extra useful registries --------------------------------------
existing_ids = {r.get("id") for r in cfg.get("registries", [])}
extra_registries = [
    {
        "id": "smithery",
        "name": "Smithery Registry",
        "description": "Community MCP server registry",
        "url": "https://smithery.ai/",
        "servers_url": "https://api.smithery.ai/servers",
        "tags": ["community"],
        "protocol": "custom/smithery",
        "provenance": "community"
    },
    {
        "id": "glama",
        "name": "Glama MCP Directory",
        "description": "Curated directory of MCP servers",
        "url": "https://glama.ai/mcp/",
        "servers_url": "https://glama.ai/api/mcp/servers",
        "tags": ["community", "curated"],
        "protocol": "custom/glama",
        "provenance": "community"
    }
]
for r in extra_registries:
    if r["id"] not in existing_ids:
        cfg.setdefault("registries", []).append(r)

# ---- Timestamp --------------------------------------------------------------
cfg["_audit_source"] = "code-audit-2026-07-28"

# Atomic write
bak = f"{CONFIG_PATH}.bak.{int(datetime.now().timestamp())}"
shutil.copy2(CONFIG_PATH, bak)
tmp = f"{CONFIG_PATH}.tmp"
with open(tmp, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
os.replace(tmp, CONFIG_PATH)
print(f"Wrote corrected max-yolo config to {CONFIG_PATH}")
print(f"Backup at {bak}")
