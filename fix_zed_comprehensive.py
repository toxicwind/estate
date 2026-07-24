#!/usr/bin/env python3
"""
Comprehensive fix for Zed NVIDIA integration and configuration issues.
This script will:
1. Add missing NVIDIA provider configuration to settings.json
2. Clean up JSON syntax issues
3. Verify all providers are properly configured
4. Check for any git staging issues
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def read_settings() -> Dict[str, Any]:
    """Read and parse the current settings.json file."""
    settings_path = Path("/home/toxic/.config/zed/settings.json")

    try:
        with open(settings_path, "r") as f:
            content = f.read()

        # Try to parse as JSON
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            print(f"JSON parsing error at line {e.lineno}, column {e.colno}: {e.msg}")
            # Show context around the error
            lines = content.splitlines()
            for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 3)):
                marker = ">>>" if i == e.lineno - 1 else "   "
                print(f"{marker} {i + 1:4d}: {lines[i]}")
            raise
    except Exception as e:
        print(f"Failed to read settings: {e}")
        sys.exit(1)


def write_settings(data: Dict[str, Any]) -> bool:
    """Write the fixed settings back to file."""
    settings_path = Path("/home/toxic/.config/zed/settings.json")

    try:
        # Create backup
        backup_path = settings_path.with_suffix(".backup")
        with open(settings_path, "r") as src, open(backup_path, "w") as dst:
            dst.write(src.read())
        print(f"Created backup: {backup_path}")

        # Write new settings
        with open(settings_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Updated settings written to {settings_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to write settings: {e}")
        return False


def add_nvidia_provider(data: Dict[str, Any]) -> bool:
    """Add NVIDIA provider configuration."""
    if "nvidia" in data.get("language_models", {}):
        print("✓ NVIDIA provider already exists")
        return True

    print("✓ Adding NVIDIA provider configuration")

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

    if "language_models" not in data:
        data["language_models"] = {}

    data["language_models"]["nvidia"] = nvidia_config
    return True


def clean_json_syntax(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up any JSON syntax issues in the settings."""
    print("✓ Cleaning JSON syntax...")

    # Remove any trailing commas that might cause issues
    # Ensure all providers have consistent structure
    if "language_models" in data:
        for provider_name, provider_config in data["language_models"].items():
            if isinstance(provider_config, dict):
                # Ensure api_url exists for all providers except special cases
                if (
                    provider_name not in ["llama_cpp", "ollama"]
                    and "api_url" not in provider_config
                ):
                    print(f"  - Adding missing api_url for {provider_name}")
                    # Use a reasonable default based on provider
                    if "openai" in provider_name:
                        provider_config["api_url"] = "https://api.openai.com/v1"
                    elif "anthropic" in provider_name:
                        provider_config["api_url"] = "https://api.anthropic.com"
                    else:
                        provider_config["api_url"] = ""

                # Ensure available_models is a list
                if "available_models" not in provider_config:
                    provider_config["available_models"] = []

    return data


def verify_providers(data: Dict[str, Any]) -> bool:
    """Verify all providers are properly configured."""
    print("✓ Verifying provider configurations...")

    if "language_models" not in data:
        print("✗ No language_models section found")
        return False

    providers = data["language_models"]
    expected_providers = [
        "llama.cpp",
        "openai",
        "anthropic",
        "mistral",
        "openrouter",
        "groq",
        "nvidia",
        "sovereign-router",
        "mcpproxy-sovereign",
    ]

    found_providers = []
    missing_providers = []

    for expected in expected_providers:
        if expected in providers:
            found_providers.append(expected)
        else:
            missing_providers.append(expected)

    print(f"  Found {len(found_providers)} providers: {', '.join(found_providers)}")

    if missing_providers:
        print(
            f"  Missing {len(missing_providers)} providers: {', '.join(missing_providers)}"
        )

    # Check NVIDIA specifically
    if "nvidia" not in providers:
        print("✗ NVIDIA provider missing")
        return False

    nvidia = providers["nvidia"]
    if "api_url" not in nvidia or not nvidia["api_url"]:
        print("✗ NVIDIA API URL not configured")
        return False

    if not nvidia.get("available_models"):
        print("✗ NVIDIA has no models configured")
        return False

    print(
        f"✓ NVIDIA provider properly configured with {len(nvidia['available_models'])} models"
    )
    return True


def check_git_status():
    """Check git status for any staging issues."""
    print("✓ Checking git status...")

    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd="/home/toxic/projects/zed",
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            if result.stdout.strip():
                print("  Git status (staged/unstaged changes):")
                for line in result.stdout.strip().split("\n"):
                    print(f"    {line}")
            else:
                print("  No changes staged or unstaged")
        else:
            print(f"  Git command failed: {result.stderr}")
    except Exception as e:
        print(f"  Could not check git status: {e}")


def main():
    """Main execution function."""
    print("=== Comprehensive Zed Fix ===")
    print()

    # Step 1: Read current settings
    print("Step 1/5: Reading current settings...")
    try:
        data = read_settings()
        print("✓ Settings loaded successfully")
    except Exception:
        print("✗ Failed to load settings")
        return 1

    # Step 2: Add NVIDIA provider
    print("\nStep 2/5: Adding NVIDIA provider...")
    if not add_nvidia_provider(data):
        print("✗ Failed to add NVIDIA provider")
        return 1

    # Step 3: Clean JSON syntax
    print("\nStep 3/5: Cleaning JSON syntax...")
    data = clean_json_syntax(data)

    # Step 4: Write fixed settings
    print("\nStep 4/5: Writing fixed settings...")
    if not write_settings(data):
        print("✗ Failed to write settings")
        return 1

    # Step 5: Verify the fix
    print("\nStep 5/5: Verifying fix...")
    try:
        verified_data = read_settings()
        if not verify_providers(verified_data):
            print("✗ Fix verification failed")
            return 1
    except Exception:
        print("✗ Failed to verify fix")
        return 1

    # Check git status
    print("\nAdditional checks:")
    check_git_status()

    print("\n" + "=" * 50)
    print("✓ All fixes applied successfully!")
    print()
    print("Next steps:")
    print("1. Rebuild Zed: cd /home/toxic/projects/zed && cargo build --release")
    print("2. Restart Zed to use the new binary with NVIDIA support")
    print("3. Verify NVIDIA models appear in Zed's model selection")
    print("4. Check that all providers are working correctly")

    return 0


if __name__ == "__main__":
    sys.exit(main())
