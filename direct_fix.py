#!/usr/bin/env python3
"""
Direct fix for Zed settings.json - adds NVIDIA provider
"""

import json
import sys
from pathlib import Path


def main():
    settings_path = Path("/home/toxic/.config/zed/settings.json")
    backup_path = Path("/home/toxic/.config/zed/settings.json.direct_fix_backup")

    print("=== Direct Zed Settings Fix ===")

    # Create backup
    print("1. Creating backup...")
    with open(settings_path, "r") as src, open(backup_path, "w") as dst:
        content = src.read()
        dst.write(content)
    print(f"   Backup created: {backup_path}")

    # Parse JSON
    print("2. Parsing settings...")
    try:
        data = json.loads(content)
        print("   ✓ JSON parsed successfully")
    except json.JSONDecodeError as e:
        print(f"   ✗ JSON parse error: {e}")
        return 1

    # Add NVIDIA provider
    print("3. Adding NVIDIA provider...")
    nvidia_config = {
        "api_url": "https://integrate.api.nvidia.com/v1",
        "available_models": [
            {
                "name": "thinkingmachines/inkling",
                "display_name": "NVIDIA NIM • Inkling SUDO MAX",
                "max_tokens": 1048576,
                "max_output_tokens": 2383,
                "reasoning_effort": "max",
                "capabilities": {
                    "tools": True,
                    "images": False,
                    "parallel_tool_calls": True,
                    "prompt_cache_key": False,
                    "chat_completions": True,
                    "interleaved_reasoning": True,
                    "max_tokens_parameter": True,
                },
            },
            {
                "name": "nvidia/nemotron-3-ultra-550b-a55b",
                "display_name": "NVIDIA • Nemotron 3 Ultra 550B",
                "max_tokens": 131072,
                "max_output_tokens": 16384,
                "capabilities": {
                    "tools": True,
                    "images": False,
                    "parallel_tool_calls": True,
                    "prompt_cache_key": False,
                    "chat_completions": True,
                    "interleaved_reasoning": False,
                    "max_tokens_parameter": True,
                },
            },
        ],
    }

    # Ensure language_models section exists
    if "language_models" not in data:
        data["language_models"] = {}

    # Add NVIDIA provider
    data["language_models"]["nvidia"] = nvidia_config
    print("   ✓ NVIDIA provider added")

    # Write back
    print("4. Writing updated settings...")
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"   ✓ Settings written to {settings_path}")

    # Verify
    print("5. Verifying changes...")
    with open(settings_path, "r") as f:
        verified_data = json.load(f)

    if "nvidia" in verified_data.get("language_models", {}):
        nvidia = verified_data["language_models"]["nvidia"]
        print(f"   ✓ NVIDIA provider verified")
        print(f"   ✓ API URL: {nvidia['api_url']}")
        print(f"   ✓ Models: {len(nvidia['available_models'])}")
    else:
        print("   ✗ NVIDIA provider not found after update")
        return 1

    print("\n" + "=" * 50)
    print("✓ SUCCESS: NVIDIA provider added to Zed settings")
    print("\nNext steps:")
    print("1. Rebuild Zed: cd /home/toxic/projects/zed && cargo build --release")
    print("2. Restart Zed to use the new binary with NVIDIA support")
    print("3. Verify NVIDIA models appear in Zed's model selection")

    return 0


if __name__ == "__main__":
    sys.exit(main())
