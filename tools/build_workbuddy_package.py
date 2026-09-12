#!/usr/bin/env python3
"""Build and validate the local WorkBuddy delivery package."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "workbuddy" / "zhj-testing-expert"
SKILLS = ROOT / "ZHJ_test_skills"
DELIVERABLES = ROOT / "deliverables"
STAGING = DELIVERABLES / "ZHJ_test_skills_WorkBuddy" / "zhj-testing-expert"
ARCHIVE = DELIVERABLES / "ZHJ_test_skills_WorkBuddy.zip"
EXCLUDED_NAMES = {"mysql_config.json", "records.jsonl"}


def ignored(path: Path) -> bool:
    return path.name in EXCLUDED_NAMES or ".git" in path.parts or "__pycache__" in path.parts


def copy_tree(source: Path, target: Path) -> None:
    for item in source.rglob("*"):
        if ignored(item):
            continue
        destination = target / item.relative_to(source)
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def validate(package: Path) -> None:
    manifest = json.loads((package / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest["version"] != "1.1.0" or len(manifest["tags"]) != 3 or len(manifest["quickPrompts"]) != 3:
        raise ValueError("WorkBuddy manifest version, tags, or quick prompts are invalid")
    required = [
        "agents/zhj-testing-expert.md",
        "avatars/zhj-testing-expert.svg",
        "references/eight-stage-prompts.md",
        "skills/ZHJ_test_skills/SKILL.md",
    ]
    missing = [entry for entry in required if not (package / entry).exists()]
    if missing:
        raise ValueError(f"Missing package files: {', '.join(missing)}")


def main() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)
    copy_tree(SOURCE, STAGING)
    copy_tree(SKILLS, STAGING / "skills" / "ZHJ_test_skills")
    validate(STAGING)
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in STAGING.rglob("*"):
            if item.is_file() and not ignored(item):
                archive.write(item, item.relative_to(STAGING.parent))
    print(ARCHIVE)


if __name__ == "__main__":
    main()
