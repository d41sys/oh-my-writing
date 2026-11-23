"""Tests for bin/oh-my-writing.mjs (the npx installer).

Every run uses a temp HOME; the real HOME is never touched.
Run: python -m pytest tests/installer -q
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "bin" / "oh-my-writing.mjs"
SKILLS = sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").exists())

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    return h


def run(home, *args):
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    return subprocess.run(
        ["node", str(CLI), *args], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120
    )


def tree(home):
    """Snapshot of every path under home with its kind and link target."""
    out = {}
    for p in sorted(home.rglob("*")):
        rel = p.relative_to(home).as_posix()
        out[rel] = ("link", os.readlink(p)) if p.is_symlink() else ("dir",) if p.is_dir() else ("file", p.stat().st_size)
    return out


def make_foreign(home):
    foreign = home / ".claude" / "skills" / "author-voice"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("mine\n")
    return foreign


def test_fresh_install_links_every_skill_per_host(home):
    r = run(home, "install", "--yes")
    assert r.returncode == 0, r.stderr
    store = home / ".oh-my-writing" / "skills"
    for host_dir in (home / ".agents" / "skills", home / ".claude" / "skills"):
        links = [p for p in host_dir.iterdir() if p.is_symlink()]
        assert sorted(p.name for p in links) == SKILLS
        for p in links:
            assert Path(os.readlink(p)) == store / p.name
            assert (p / "SKILL.md").exists()
    assert (home / ".oh-my-writing" / "VERSION").read_text().strip() == json.loads((REPO / "package.json").read_text())["version"]
    assert (home / ".oh-my-writing" / "manifest.json").exists()
    assert "Verify" in r.stdout


def test_default_command_is_install(home):
    assert run(home, "--yes").returncode == 0
    assert (home / ".agents" / "skills" / SKILLS[0]).is_symlink()


def test_store_copy_excludes_junk(home):
    assert run(home, "install", "--yes").returncode == 0
    store = home / ".oh-my-writing" / "skills"
    names = {p.name for p in store.rglob("*")}
    assert not names & {"__pycache__", ".DS_Store", "tests"}


def test_hosts_flag_limits_dirs(home):
    assert run(home, "install", "--yes", "--hosts", "claude").returncode == 0
    assert len(list((home / ".claude" / "skills").iterdir())) == len(SKILLS)
    assert not (home / ".agents").exists()
    assert run(home, "install", "--yes", "--hosts=codex").returncode == 0
    assert len(list((home / ".agents" / "skills").iterdir())) == len(SKILLS)


def test_copy_mode_makes_real_folders(home):
    assert run(home, "install", "--yes", "--copy").returncode == 0
    for host_dir in (home / ".agents" / "skills", home / ".claude" / "skills"):
        for name in SKILLS:
            p = host_dir / name
            assert p.is_dir() and not p.is_symlink() and (p / "SKILL.md").exists()
    assert run(home, "uninstall", "--yes").returncode == 0
    assert not (home / ".agents" / "skills" / SKILLS[0]).exists()


def test_foreign_folder_blocks_install_without_force(home):
    foreign = home / ".claude" / "skills" / "author-voice"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("mine\n")
    before = tree(home)
    r = run(home, "install", "--yes")
    assert r.returncode == 1
    assert "author-voice" in r.stderr and "--force" in r.stderr
    assert tree(home) == before  # nothing changed, not even the store


def test_force_backs_up_foreign_folder_and_replaces(home):
    foreign = home / ".claude" / "skills" / "author-voice"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("mine\n")
    r = run(home, "install", "--yes", "--force")
    assert r.returncode == 0, r.stderr
    assert foreign.is_symlink()
    (backup,) = list((home / ".oh-my-writing" / "backup").iterdir())
    assert (backup / "claude-skills" / "author-voice" / "SKILL.md").read_text() == "mine\n"


def test_uninstall_removes_only_own_entries(home):
    other = home / ".claude" / "skills" / "someone-elses-skill"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("keep\n")
    assert run(home, "install", "--yes").returncode == 0
    # user swaps one of our links for their own folder: uninstall must leave it
    swapped = home / ".agents" / "skills" / "post-writing"
    swapped.unlink()
    swapped.mkdir()
    (swapped / "SKILL.md").write_text("user replaced\n")
    r = run(home, "uninstall", "--yes")
    assert r.returncode == 0, r.stderr
    assert (other / "SKILL.md").read_text() == "keep\n"
    assert (swapped / "SKILL.md").read_text() == "user replaced\n"
    assert [p.name for p in (home / ".agents" / "skills").iterdir()] == ["post-writing"]
    assert [p.name for p in (home / ".claude" / "skills").iterdir()] == ["someone-elses-skill"]
    assert not (home / ".oh-my-writing" / "manifest.json").exists()
    assert not (home / ".oh-my-writing" / "skills").exists()


def test_uninstall_restore_brings_backed_up_folder_back(home):
    foreign = make_foreign(home)
    assert run(home, "install", "--yes", "--force").returncode == 0
    r = run(home, "uninstall", "--restore", "--yes")
    assert r.returncode == 0, r.stderr
    assert not foreign.is_symlink() and (foreign / "SKILL.md").read_text() == "mine\n"
    assert not (home / ".oh-my-writing").exists()
    assert not list((home / ".agents" / "skills").iterdir())


def test_uninstall_without_restore_keeps_backup(home):
    foreign = make_foreign(home)
    assert run(home, "install", "--yes", "--force").returncode == 0
    assert run(home, "uninstall", "--yes").returncode == 0
    assert not foreign.exists()
    assert len(list((home / ".oh-my-writing" / "backup").iterdir())) == 1


def test_dry_run_changes_nothing(home):
    make_foreign(home)
    before = tree(home)
    r = run(home, "install", "--dry-run", "--yes", "--force")
    assert r.returncode == 0, r.stderr
    assert "dry run" in r.stdout.lower()
    assert tree(home) == before
    assert not (home / ".oh-my-writing").exists()
    # uninstall dry run after a real install changes nothing either
    assert run(home, "install", "--yes", "--force").returncode == 0
    before = tree(home)
    r = run(home, "uninstall", "--restore", "--dry-run")
    assert r.returncode == 0, r.stderr
    assert tree(home) == before


def test_doctor_reports_broken_link(home):
    assert run(home, "install", "--yes").returncode == 0
    ok = run(home, "doctor")
    assert ok.returncode == 0, ok.stdout
    shutil.rmtree(home / ".oh-my-writing" / "skills" / "post-writing")
    r = run(home, "doctor")
    assert r.returncode == 1
    assert "Broken link" in r.stdout and "post-writing" in r.stdout
    assert "BROKEN" in run(home, "list").stdout


def test_doctor_warns_on_plugin_cache_duplicate(home):
    assert run(home, "install", "--yes").returncode == 0
    dup = home / ".claude" / "plugins" / "cache" / "mkt" / "oh-my-writing" / "2.0.0" / "skills" / "author-voice"
    dup.mkdir(parents=True)
    (dup / "SKILL.md").write_text("dup\n")
    r = run(home, "doctor")
    assert r.returncode == 0
    assert "Duplicate skill author-voice" in r.stdout


def test_list_shows_hosts(home):
    assert run(home, "install", "--yes", "--hosts", "claude").returncode == 0
    r = run(home, "list")
    assert r.returncode == 0
    row = next(line for line in r.stdout.splitlines() if line.startswith("author-voice"))
    cols = row.split()
    assert cols[1:] == ["yes", "-", "yes"]  # claude, codex, omp


def test_reinstall_is_idempotent(home):
    assert run(home, "install", "--yes").returncode == 0
    before = tree(home)
    assert run(home, "install", "--yes").returncode == 0
    assert tree(home) == before


def test_with_diagram_design_without_git_warns_not_fails(home, tmp_path):
    node = shutil.which("node")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "node").symlink_to(node)
    env = {**os.environ, "HOME": str(home), "PATH": str(bindir)}
    r = subprocess.run(
        [str(bindir / "node"), str(CLI), "install", "--yes", "--with-diagram-design"],
        env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    assert "git not found" in r.stdout
    assert not (home / ".agents" / "skills" / "diagram-design").exists()
    assert len(list((home / ".agents" / "skills").iterdir())) == len(SKILLS)


def test_unknown_flag_is_usage_error(home):
    r = run(home, "install", "--nope")
    assert r.returncode == 2
    assert "unknown flag" in r.stderr


def test_with_diagram_design_clones_and_links(home, tmp_path):
    fake = tmp_path / "fakebin"
    fake.mkdir()
    git = fake / "git"
    git.write_text(
        '#!/bin/sh\n'
        '[ "$1" = "--version" ] && exit 0\n'
        'for last; do :; done\n'
        'mkdir -p "$last/skills/diagram-design" && echo "# fake" > "$last/skills/diagram-design/SKILL.md"\n'
        'echo "$@" > "$last/.args"\n'
    )
    git.chmod(0o755)
    env = {**os.environ, "HOME": str(home), "PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"}
    r = subprocess.run(
        ["node", str(CLI), "install", "--yes", "--with-diagram-design"],
        env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    clone = home / ".oh-my-writing" / "diagram-design"
    assert "https://github.com/cathrynlavery/diagram-design" in (clone / ".args").read_text()
    for host_dir in (home / ".agents" / "skills", home / ".claude" / "skills"):
        link = host_dir / "diagram-design"
        assert link.is_symlink() and Path(os.readlink(link)) == clone / "skills" / "diagram-design"
    r = subprocess.run(["node", str(CLI), "uninstall", "--yes"], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0
    assert not (home / ".agents" / "skills" / "diagram-design").exists()
    assert clone.exists()  # the clone is left for the user to delete
