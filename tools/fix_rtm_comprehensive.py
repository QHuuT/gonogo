#!/usr/bin/env python3
"""
Comprehensive fix for rtm.py syntax errors from automated reformatting.
"""

import re
from pathlib import Path


def fix_rtm_comprehensive():
    """Apply comprehensive fixes to rtm.py."""
    file_path = Path(__file__).parent.parent / "src" / "be" / "api" / "rtm.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix decorator indentation - remove extra spaces before @router
    content = re.sub(r"^[ ]+(@router\.)", r"\1", content, flags=re.MULTILINE)

    # Fix function definitions with inline docstrings
    content = re.sub(
        r'def ([^:]+):\s*"""([^"]+)"""\s*\n',
        r'def \1:\n    """\2"""\n',
        content,
        flags=re.MULTILINE,
    )

    # Fix broken if/for statements that got concatenated
    content = re.sub(
        r"(\w+)\s*:\s*(\w+.*?)\s+(for\s+\w+\s+in)",
        r"\1:\n        \2\n        \3",
        content,
    )
    content = re.sub(
        r"(\w+)\s*:\s*(\w+.*?)\s+(if\s+\w+)", r"\1:\n        \2\n        \3", content
    )

    # Fix component filtering sections that got mangled
    fixes = [
        # Fix if statements that lost their newlines
        ("if component: components =", "if component:\n        components ="),
        (
            "if exclude_component: exclude_components =",
            "if exclude_component:\n        exclude_components =",
        ),
        (
            "if not epic: raise HTTPException",
            "if not epic:\n        raise HTTPException",
        ),
        (
            "if not test: raise HTTPException",
            "if not test:\n        raise HTTPException",
        ),
        # Fix broken for loops
        (
            "component_filters = [] for comp in components:",
            "component_filters = []\n        for comp in components:",
        ),
        # Fix elif statements
        (
            "return HTMLResponse(content=content) elif format",
            "return HTMLResponse(content=content)\n    elif format",
        ),
        (
            "content = \
            generator.generate_markdown_matrix(filters) return Response",
            "content = generator.generate_markdown_matrix(filters)\n        return Response",
        ),
        # Fix broken dictionary definitions
        ('{ "epic_id": epic_id,', '{\n        "epic_id": epic_id,'),
        ('{ "severity": severity_filter,', '{\n        "severity": severity_filter,'),
        # Fix broken return statements with multiple values
        (
            '"timestamp": datetime.now(datetime.UTC).isoformat(), "epic_status":',
            '"timestamp": datetime.now(datetime.UTC).isoformat(),\n        "epic_status":',
        ),
        (
            '"persona": persona.upper(), "metrics":',
            '"persona": persona.upper(),\n            "metrics":',
        ),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # Fix broken string literals across lines
    content = re.sub(
        r'description="([^"]*)\n([^"]*)"',
        r'description="\1 \2"',
        content,
        flags=re.MULTILINE,
    )

    # Remove extra trailing spaces and normalize whitespace
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Applied comprehensive fixes to rtm.py")


if __name__ == "__main__":
    fix_rtm_comprehensive()
