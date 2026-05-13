"""Core matching engine: loads skills and matches symptoms to solutions."""

import os
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def _parse_yaml_simple(text):
    """Minimal YAML-like parser for when PyYAML is not installed."""
    # This handles the flat structure enough to load skill files
    # For full fidelity, install PyYAML
    import json
    # Try json first (won't work for YAML but worth a shot for simple cases)
    lines = text.splitlines()
    result = {}
    current_key = None
    current_list = None
    indent_stack = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())

        # Top-level key: value
        if indent == 0 and ":" in stripped and not stripped.startswith("-"):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val
            else:
                result[key] = []
            current_key = key
            current_list = result[key] if isinstance(result[key], list) else None
            continue

        # List item
        if stripped.startswith("- ") and current_key:
            item = stripped[2:].strip().strip('"').strip("'")
            if isinstance(result.get(current_key), list):
                result[current_key].append(item)

    return result


def load_skills(skills_dir=None):
    """Load all YAML skill files from the skills directory."""
    if skills_dir is None:
        skills_dir = Path(__file__).parent / "skills"
    else:
        skills_dir = Path(skills_dir)

    skills = []
    for f in sorted(skills_dir.glob("*.yaml")):
        text = f.read_text()
        if yaml:
            data = yaml.safe_load(text) or {}
        else:
            data = _parse_yaml_simple(text)
        data["_file"] = str(f)
        skills.append(data)
    return skills


def match_skills(query, skills, threshold=0.1):
    """Match a query string against loaded skills. Returns sorted list of (score, skill)."""
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    results = []

    for skill in skills:
        score = 0.0

        # Check symptoms (highest weight)
        for symptom in skill.get("symptoms", []):
            if isinstance(symptom, str) and symptom.lower() in query_lower:
                score += 3.0

        # Check keywords
        for kw in skill.get("keywords", []):
            if isinstance(kw, str) and kw.lower() in query_lower:
                score += 2.0

        # Check title
        title = skill.get("title", "")
        title_words = set(re.findall(r'\w+', title.lower()))
        overlap = query_words & title_words
        if overlap:
            score += len(overlap) * 1.0

        # Check category
        cat = skill.get("category", "")
        if cat and cat.lower() in query_lower:
            score += 1.5

        if score >= threshold:
            results.append((score, skill))

    results.sort(key=lambda x: -x[0])
    return results
