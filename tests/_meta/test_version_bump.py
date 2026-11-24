"""A skill whose files changed since a base commit must carry a new metadata.version.

Runs only when OMW_BASE_REF names a commit (CI sets it to the pull request base or the previous push):
    OMW_BASE_REF=origin/main uv run --with pytest --with pyyaml python -m pytest tests/_meta -q
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BASE = os.environ.get("OMW_BASE_REF", "")
VERSION_RE = re.compile(r"(?m)^\s+version:\s*\"?([^\"\n]+)")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def version(text: str) -> str | None:
    m = VERSION_RE.search(text.split("\n---", 2)[0])
    return m.group(1).strip() if m else None


@pytest.mark.skipif(not BASE or git("rev-parse", "--verify", f"{BASE}^{{commit}}").returncode != 0,
                    reason="OMW_BASE_REF is not set to a commit")
def test_changed_skills_bump_their_version():
    changed = git("diff", "--name-only", BASE, "--", "skills").stdout.split()
    stale = []
    for name in sorted({p.split("/")[1] for p in changed if p.count("/") >= 2}):
        skill_md = REPO / "skills" / name / "SKILL.md"
        old = git("show", f"{BASE}:skills/{name}/SKILL.md")
        if not skill_md.is_file() or old.returncode != 0:  # removed or new skill
            continue
        if version(old.stdout) == version(skill_md.read_text(encoding="utf-8")):
            stale.append(name)
    assert not stale, f"changed without a metadata.version bump: {stale}"
