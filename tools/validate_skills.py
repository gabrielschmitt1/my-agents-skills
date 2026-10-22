#!/usr/bin/env python3
"""Valida skills e agentes do repositório: frontmatter, links, JSON e testes.

Uso:
    python3 tools/validate_skills.py
    python3 tools/validate_skills.py --no-tests
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"`((?:references|templates|assets|scripts)/[^`\s]+)`")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def find_skills() -> list[Path]:
    """Skills em skills/ e agentes em agents/ (ambos com SKILL.md)."""
    skills: list[Path] = []
    for base in (ROOT / "skills", ROOT / "agents"):
        if not base.is_dir():
            continue
        for path in sorted(base.iterdir()):
            if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").is_file():
                skills.append(path)
    return skills


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        data[key.strip()] = value.strip().strip("\"'")
    return data


def check_skill(skill: Path, run_tests: bool) -> list[str]:
    errors: list[str] = []
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    meta = parse_frontmatter(text)

    name = meta.get("name", "")
    description = meta.get("description", "")
    if not name:
        errors.append("SKILL.md sem 'name' no frontmatter")
    elif name != skill.name:
        errors.append(f"name {name!r} difere da pasta {skill.name!r}")
    if len(description) < 20:
        errors.append("SKILL.md sem 'description' útil no frontmatter")

    if not (skill / "README.md").is_file():
        errors.append("falta README.md")

    for link in sorted(set(LINK_RE.findall(text))):
        if any(char in link for char in "*?[]"):
            continue
        if not (skill / link).exists():
            errors.append(f"link quebrado no SKILL.md: {link}")

    assets = skill / "assets"
    if assets.is_dir():
        for path in sorted(assets.glob("*.json")):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"JSON inválido em {path.relative_to(skill)}: {exc}")

    if run_tests and (skill / "tests").is_dir():
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=skill,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            tail = (result.stderr or result.stdout).strip().splitlines()[-8:]
            errors.append("testes falharam:\n    " + "\n    ".join(tail))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida todas as skills do repositório.")
    parser.add_argument("--no-tests", action="store_true", help="Não roda os testes unitários.")
    args = parser.parse_args()

    skills = find_skills()
    if not skills:
        print("Nenhuma skill/agente encontrado (pasta com SKILL.md).", file=sys.stderr)
        return 1

    failures = 0
    for skill in skills:
        errors = check_skill(skill, run_tests=not args.no_tests)
        if errors:
            failures += 1
            print(f"FALHOU  {skill.relative_to(ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK      {skill.relative_to(ROOT)}")

    print(f"\n{len(skills) - failures}/{len(skills)} artefatos válidos.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
