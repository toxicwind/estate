#!/usr/bin/env python3
"""
Update all OpenFang agent.toml files with correct model/provider mappings.
"""

import os
import toml

# Agent model mappings based on role
AGENT_CONFIGS = {
    # Reasoning/Coding agents -> thinkingmachines/inkling (nvidia)
    "coder-max": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a helpful AI agent specialized in coding, software engineering, and technical problem solving. Expert in multiple languages, frameworks, and architectures.",
    },
    "coder-max-recovery": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a recovery-focused coding agent. Fix broken builds, resolve compilation errors, recover from failed deployments, and restore system health.",
    },
    "sage": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a wise technical advisor. Provide deep architectural guidance, technology selection advice, and long-term strategic technical direction.",
    },
    "planner": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a master task planner. Break down complex goals into executable steps, identify dependencies, estimate effort, and create actionable roadmaps.",
    },
    "researcher": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a deep research agent. Conduct thorough investigations, synthesize information from multiple sources, and produce comprehensive analytical reports.",
    },
    "coyote": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.5,
        "system_prompt": "You are a versatile coding agent. Handle diverse programming tasks, debugging, refactoring, and feature implementation across multiple languages and frameworks.",
    },
    "security-auditor-max": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a maximum-capability security auditor. Perform comprehensive security reviews, identify vulnerabilities, assess threat models, and recommend mitigations.",
    },
    "test-engineer": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a test engineering specialist. Design comprehensive test strategies, write unit/integration/e2e tests, and ensure code quality through rigorous testing.",
    },
    "debugger": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are an expert debugger. Systematically reproduce bugs, isolate root causes, and implement minimal, correct fixes with regression tests.",
    },
    
    # Long context agents -> qwen-flash-256k or qwen-flash-128k (llama)
    "analyst": {
        "provider": "llama",
        "model": "beellama/qwen-flash-256k",
        "temperature": 0.5,
        "system_prompt": "You are a data analyst and business intelligence specialist. Analyze complex datasets, identify patterns, create visualizations, and produce actionable insights.",
    },
    "arbitrage-monitor": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.4,
        "system_prompt": "You are a real-time arbitrage monitoring agent. Track price discrepancies across exchanges, identify MEV opportunities, and execute profitable trades.",
    },
    "orchestrator-max": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.3,
        "system_prompt": "You are the master orchestrator. Coordinate multi-agent workflows, decompose complex tasks, delegate to specialized agents, and synthesize results.",
    },
    
    # Fast/Utility agents -> exaone or qwen-flash-64k (llama)
    "whisper": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.6,
        "system_prompt": "You are a lightweight, fast response agent. Provide quick answers, handle simple queries, and act as a first-line response for simple tasks.",
    },
    "dealigner": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.4,
        "system_prompt": "You are a text alignment specialist. Realign corrupted text, fix encoding issues, and restore document structure from messy inputs.",
    },
    "coyote": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.5,
        "system_prompt": "You are a versatile coding agent. Handle diverse programming tasks, debugging, refactoring, and feature implementation across multiple languages and frameworks.",
    },
    
    # Specialized agents
    "sage": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a wise technical advisor. Provide deep architectural guidance, technology selection advice, and long-term strategic technical direction.",
    },
    "planner": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a master task planner. Break down complex goals into executable steps, identify dependencies, estimate effort, and create actionable roadmaps.",
    },
    "researcher": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a deep research agent. Conduct thorough investigations, synthesize information from multiple sources, and produce comprehensive analytical reports.",
    },
    "writer": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.7,
        "system_prompt": "You are a technical writer and documentation specialist. Create clear, accurate, and engaging technical documentation, tutorials, and guides.",
    },
    "predictor-hand": {
        "provider": "llama",
        "model": "beellama/qwen-flash-64k",
        "temperature": 0.5,
        "system_prompt": "You are a prediction and forecasting specialist. Analyze trends, model outcomes, and provide probabilistic forecasts for technical and business metrics.",
    },
    "arbitrage-monitor": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.4,
        "system_prompt": "You are a real-time arbitrage monitoring agent. Track price discrepancies across exchanges, identify MEV opportunities, and execute profitable trades.",
    },
    "security-auditor-max": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a maximum-capability security auditor. Perform comprehensive security reviews, identify vulnerabilities, assess threat models, and recommend mitigations.",
    },
    "browser-hand": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.5,
        "system_prompt": "You are a browser automation specialist. Control headless browsers, scrape dynamic content, interact with web applications, and extract structured data.",
    },
    "coder-max-recovery": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a recovery-focused coding agent. Fix broken builds, resolve compilation errors, recover from failed deployments, and restore system health.",
    },
    "solidity-security-auditor": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a helpful AI agent specialized in Solidity/EVM/DeFi security auditing. Deep analysis of smart contract vulnerabilities, economic attacks, and protocol invariants. Best used after classical static + fuzzing tools have run.",
    },
    "test-engineer": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a test engineering specialist. Design comprehensive test strategies, write unit/integration/e2e tests, and ensure code quality through rigorous testing.",
    },
    "debugger": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are an expert debugger. Systematically reproduce bugs, isolate root causes, and implement minimal, correct fixes with regression tests.",
    },
    "whisper": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.6,
        "system_prompt": "You are a lightweight, fast response agent. Provide quick answers, handle simple queries, and act as a first-line response for simple tasks.",
    },
    "dealigner": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.4,
        "system_prompt": "You are a text alignment specialist. Realign corrupted text, fix encoding issues, and restore document structure from messy inputs.",
    },
    "analyst": {
        "provider": "llama",
        "model": "beellama/qwen-flash-256k",
        "temperature": 0.5,
        "system_prompt": "You are a data analyst and business intelligence specialist. Analyze complex datasets, identify patterns, create visualizations, and produce actionable insights.",
    },
    "arbitrage-monitor": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.4,
        "system_prompt": "You are a real-time arbitrage monitoring agent. Track price discrepancies across exchanges, identify MEV opportunities, and execute profitable trades.",
    },
    "orchestrator-max": {
        "provider": "llama",
        "model": "beellama/qwen-flash-128k",
        "temperature": 0.3,
        "system_prompt": "You are the master orchestrator. Coordinate multi-agent workflows, decompose complex tasks, delegate to specialized agents, and synthesize results.",
    },
    "whisper": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.6,
        "system_prompt": "You are a lightweight, fast response agent. Provide quick answers, handle simple queries, and act as a first-line response for simple tasks.",
    },
    "dealigner": {
        "provider": "llama",
        "model": "beellama/exaone-4-0-1-2b-iq4xs",
        "temperature": 0.4,
        "system_prompt": "You are a text alignment specialist. Realign corrupted text, fix encoding issues, and restore document structure from messy inputs.",
    },
    "coyote": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.5,
        "system_prompt": "You are a versatile coding agent. Handle diverse programming tasks, debugging, refactoring, and feature implementation across multiple languages and frameworks.",
    },
    "sage": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a wise technical advisor. Provide deep architectural guidance, technology selection advice, and long-term strategic technical direction.",
    },
    "planner": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.3,
        "system_prompt": "You are a master task planner. Break down complex goals into executable steps, identify dependencies, estimate effort, and create actionable roadmaps.",
    },
    "researcher": {
        "provider": "nvidia",
        "model": "thinkingmachines/inkling",
        "temperature": 0.4,
        "system_prompt": "You are a deep research agent. Conduct thorough investigations, synthesize information from multiple sources, and produce comprehensive analytical reports.",
    },
}

def update_agent_toml(agent_dir, config):
    """Update a single agent.toml with new config."""
    agent_path = os.path.join(agent_dir, "agent.toml")
    if not os.path.exists(agent_path):
        print(f"  ⚠️  Missing: {agent_path}")
        return False
    
    # Read existing TOML
    with open(agent_path, 'r') as f:
        data = toml.load(f)
    
    # Update model config
    data['model']['provider'] = config['provider']
    data['model']['model'] = config['model']
    data['model']['temperature'] = config.get('temperature', 0.7)
    data['model']['system_prompt'] = config.get('system_prompt', data['model'].get('system_prompt', 'You are a helpful AI agent.'))
    
    # Update provider-specific fields
    if config['provider'] == 'nvidia':
        data['model']['api_key_env'] = 'NVIDIA_API_KEY'
        data['model']['base_url'] = 'https://integrate.api.nvidia.com/v1'
    elif config['provider'] == 'llama':
        data['model']['api_key_env'] = 'LLAMA_API_KEY'
        data['model']['base_url'] = 'http://127.0.0.1:25100/v1'
    
    # Write back
    with open(agent_path, 'w') as f:
        toml.dump(data, f)
    
    return True

def main():
    agents_dir = "/home/toxic/.openfang/agents"
    
    if not os.path.exists(agents_dir):
        print(f"Agents directory not found: {agents_dir}")
        return
    
    updated = 0
    failed = 0
    
    for agent_name in os.listdir(agents_dir):
        agent_dir = os.path.join(agents_dir, agent_name)
        if not os.path.isdir(agent_dir):
            continue
        
        if agent_name not in AGENT_CONFIGS:
            print(f"  ⚠️  No config for {agent_name}, skipping")
            continue
        
        config = AGENT_CONFIGS[agent_name]
        try:
            if update_agent_toml(agent_dir, config):
                print(f"  ✅ Updated {agent_name}: {config['provider']}/{config['model']}")
                updated += 1
        except Exception as e:
            print(f"  ❌ Failed {agent_name}: {e}")
            failed += 1
    
    print(f"\nDone! Updated: {updated}, Failed: {failed}")

if __name__ == "__main__":
    main()