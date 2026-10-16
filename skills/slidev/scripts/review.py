#!/usr/bin/env python3
"""Lint a slides.md against the slidev skill conventions."""

import argparse
import os
import re
import sys
from pathlib import Path


def load_slides(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _is_frontmatter_block(block: str) -> bool:
    """Check if a block looks like per-slide frontmatter (key: value lines only)."""
    lines = block.strip().splitlines()
    if not lines:
        return False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            return False
        if ":" not in stripped and not stripped.startswith("-"):
            return False
    return True


def split_slides(content: str):
    """Split slides.md into individual slides.

    Slidev uses --- on its own line as slide separators. The first ---
    pair delimits global headmatter. Per-slide frontmatter is content at
    the start of a slide block and should not be split from its slide.
    """
    parts = re.split(r"\n---\n", content)
    slides = []
    for i, block in enumerate(parts):
        block = block.strip()
        if not block:
            continue
        # Skip the global headmatter (first block starts with ---)
        if i == 0 and block.startswith("---"):
            continue
        # If this block looks like frontmatter, merge it with the next block
        if _is_frontmatter_block(block) and i + 1 < len(parts):
            merged = block + "\n\n" + parts[i + 1].strip()
            parts[i + 1] = merged
            continue
        slides.append(block)
    return slides


def check_presenter_notes(slides: list[str]) -> list[str]:
    issues = []
    for i, slide in enumerate(slides, start=1):
        if "<!--" not in slide:
            issues.append(f"Slide {i}: missing presenter notes")
        elif re.search(r"<!--\s*-->", slide):
            issues.append(f"Slide {i}: empty presenter notes")
    return issues


def check_bullet_limits(slides: list[str]) -> list[str]:
    issues = []
    for i, slide in enumerate(slides, start=1):
        lines = slide.splitlines()
        bullets = [l for l in lines if l.strip().startswith(("- ", "* "))]
        if len(bullets) > 5:
            issues.append(f"Slide {i}: {len(bullets)} bullets (max 5)")
    return issues


def check_math_sizing(slides: list[str]) -> list[str]:
    issues = []
    for i, slide in enumerate(slides, start=1):
        display_math = re.findall(r"\$\$(.*?)\$\$", slide, re.DOTALL)
        for block in display_math:
            if not re.search(r"\\(Huge|Large|huge|large)", block):
                issues.append(f"Slide {i}: display math missing sizing command")
                break
    return issues


def check_forbidden_colors(slides: list[str]) -> list[str]:
    forbidden = {"red", "green", "yellow"}
    issues = []
    for i, slide in enumerate(slides, start=1):
        for color in forbidden:
            # Match 'color: red' frontmatter but not inline text
            if re.search(rf"^color:\s*{color}\b", slide, re.MULTILINE | re.IGNORECASE):
                issues.append(f"Slide {i}: forbidden background color '{color}'")
    return issues


def check_logo_consistency(slides: list[str], project_root: Path) -> list[str]:
    issues = []
    positions = []
    for i, slide in enumerate(slides, start=1):
        match = re.search(r'class="([^"]*)"[^>]*>\s*<img[^>]*logo', slide)
        if match:
            positions.append((i, match.group(1)))
    if len(positions) > 1:
        first = positions[0][1]
        for idx, pos in positions[1:]:
            if pos != first:
                issues.append(
                    f"Slide {idx}: logo class '{pos}' differs from slide 1 ('{first}')"
                )
    return issues


def check_section_dividers(slides: list[str]) -> list[str]:
    issues = []
    last_section = 0
    for i, slide in enumerate(slides, start=1):
        if re.search(r"^layout:\s*section\b", slide, re.MULTILINE | re.IGNORECASE):
            gap = i - last_section
            if last_section > 0 and gap > 15:
                issues.append(
                    f"Slide {i}: section divider after {gap} slides (max ~12 recommended)"
                )
            last_section = i
    return issues


def check_image_paths(slides: list[str], project_root: Path) -> list[str]:
    issues = []
    for i, slide in enumerate(slides, start=1):
        for match in re.finditer(r'src="(/[^"]+)"', slide):
            path = match.group(1)
            full = project_root / path.lstrip("/")
            if not full.exists():
                issues.append(f"Slide {i}: missing image '{path}'")
    return issues


def check_inline_text_limits(slides: list[str]) -> list[str]:
    issues = []
    for i, slide in enumerate(slides, start=1):
        lines = slide.splitlines()
        for line in lines:
            stripped = line.strip()
            # Skip frontmatter, HTML, comments, and code
            if stripped.startswith(("---", "<", "<!--", "```", "::", "layout:", "color:", "theme:", "image:")):
                continue
            if len(stripped.split()) > 40 and "." in stripped:
                issues.append(f"Slide {i}: long text paragraph detected ({len(stripped.split())} words)")
                break
    return issues


def main():
    parser = argparse.ArgumentParser(description="Lint a Slidev slides.md")
    parser.add_argument("slides", nargs="?", default="slides.md", help="Path to slides.md")
    args = parser.parse_args()

    content = load_slides(args.slides)
    slides = split_slides(content)
    root = Path(args.slides).parent.resolve()

    all_issues = []
    all_issues.extend(check_presenter_notes(slides))
    all_issues.extend(check_bullet_limits(slides))
    all_issues.extend(check_math_sizing(slides))
    all_issues.extend(check_forbidden_colors(slides))
    all_issues.extend(check_logo_consistency(slides, root))
    all_issues.extend(check_section_dividers(slides))
    all_issues.extend(check_image_paths(slides, root))
    all_issues.extend(check_inline_text_limits(slides))

    if all_issues:
        print(f"Found {len(all_issues)} issue(s) in {args.slides}:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print(f"All checks passed for {args.slides} ({len(slides)} slides)")


if __name__ == "__main__":
    main()
