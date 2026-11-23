#!/usr/bin/env node
// Oh My Writing installer. Node stdlib only.
// Copies skills/* into ~/.oh-my-writing/skills, links them into the host skill folders,
// and tracks what it created in ~/.oh-my-writing/manifest.json so uninstall removes only its own entries.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const PKG_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PKG = JSON.parse(fs.readFileSync(path.join(PKG_ROOT, 'package.json'), 'utf8'));
const SRC_SKILLS = path.join(PKG_ROOT, 'skills');

const DIAGRAM = 'diagram-design';
const DIAGRAM_REPO = 'https://github.com/cathrynlavery/diagram-design';
const EXCLUDE = new Set(['__pycache__', '.DS_Store', 'tests']);
const ALL_HOSTS = ['claude', 'codex', 'omp'];
const COMMANDS = ['install', 'uninstall', 'list', 'doctor'];
const IS_WIN = process.platform === 'win32';

const USAGE = `oh-my-writing ${PKG.version}

Usage: oh-my-writing [command] [flags]

Commands:
  install      (default) copy skills to ~/.oh-my-writing and link them into the hosts
  uninstall    remove the links/copies this tool created (add --restore to bring back the backup)
  list         show installed version and which hosts see each skill
  doctor       list + check for broken links and duplicate skills

Flags:
  --hosts a,b      claude, codex, omp (default: all). codex and omp read ~/.agents/skills,
                   claude reads ~/.claude/skills (omp reads both)
  --copy           copy skills into the host folders instead of symlinking
  --dry-run        print what would happen, change nothing
  --yes, -y        do not ask for confirmation
  --force          back up and replace an existing folder that has a skill's name
  --with-diagram-design     git clone ${DIAGRAM_REPO} and link it too
  --restore        (uninstall) move the latest backup of each path back
  --help, --version
`;

// ---------- helpers ----------

class UsageError extends Error {}

function homeDir() {
  return process.env.HOME || process.env.USERPROFILE || os.homedir();
}

function makeCtx() {
  const home = homeDir();
  const root = path.join(home, '.oh-my-writing');
  return {
    home,
    root,
    store: path.join(root, 'skills'),
    versionFile: path.join(root, 'VERSION'),
    manifestFile: path.join(root, 'manifest.json'),
    backupRoot: path.join(root, 'backup'),
    diagramDir: path.join(root, DIAGRAM),
    hostDir: {
      agents: path.join(home, '.agents', 'skills'),
      claude: path.join(home, '.claude', 'skills'),
    },
  };
}

const HOST_KEYS = { claude: ['claude'], codex: ['agents'], omp: ['agents'] };
const SEEN_BY = { agents: ['codex', 'omp'], claude: ['claude', 'omp'] };

const tilde = (ctx, p) => (p === ctx.home || p.startsWith(ctx.home + path.sep) ? '~' + p.slice(ctx.home.length) : p);

const lstat = (p) => {
  try {
    return fs.lstatSync(p);
  } catch {
    return null;
  }
};
const resolves = (p) => {
  try {
    fs.statSync(p);
    return true;
  } catch {
    return false;
  }
};
const linkPointsTo = (p, target) => {
  try {
    return path.resolve(path.dirname(p), fs.readlinkSync(p)) === path.resolve(target);
  } catch {
    return false;
  }
};

function copyTree(src, dest) {
  fs.cpSync(src, dest, {
    recursive: true,
    force: true,
    filter: (s) => !EXCLUDE.has(path.basename(s)) && !s.endsWith('.pyc'),
  });
}

function removePath(p) {
  const st = lstat(p);
  if (!st) return;
  if (st.isSymbolicLink() || !st.isDirectory()) fs.unlinkSync(p);
  else fs.rmSync(p, { recursive: true, force: true });
}

function moveRaw(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  try {
    fs.renameSync(src, dest);
  } catch (e) {
    if (e.code !== 'EXDEV') throw e;
    fs.cpSync(src, dest, { recursive: true, verbatimSymlinks: true });
    removePath(src);
  }
}

function discoverSkills(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((d) => (d.isDirectory() || d.isSymbolicLink()) && fs.existsSync(path.join(dir, d.name, 'SKILL.md')))
    .map((d) => d.name)
    .sort();
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return fallback;
  }
}

function loadManifest(ctx) {
  const m = readJson(ctx.manifestFile, null);
  return m && Array.isArray(m.entries) ? m : { version: null, entries: [] };
}

function saveManifest(ctx, m) {
  fs.mkdirSync(ctx.root, { recursive: true });
  fs.writeFileSync(ctx.manifestFile, JSON.stringify(m, null, 2) + '\n');
}

async function confirm(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const answer = await new Promise((resolve) => rl.question(question, resolve));
  rl.close();
  return /^y(es)?$/i.test(answer.trim());
}

const gitAvailable = () => spawnSync('git', ['--version'], { stdio: 'ignore' }).status === 0;

// Backup: moves things into ~/.oh-my-writing/backup/<timestamp>/<key>/<name>, never deletes.
function makeBackup(ctx, dry) {
  let dir = null;
  const entries = [];
  return {
    move(src, key) {
      if (!dir) {
        const stamp = new Date().toISOString().replace(/[:.]/g, '-');
        dir = path.join(ctx.backupRoot, stamp);
        for (let n = 1; fs.existsSync(dir); n++) dir = path.join(ctx.backupRoot, `${stamp}-${n}`);
      }
      const rel = path.join(key, path.basename(src));
      const dest = path.join(dir, rel);
      if (!dry) moveRaw(src, dest);
      entries.push({ original: src, backup: rel });
      return dest;
    },
    finish() {
      if (dir && !dry && entries.length) {
        fs.writeFileSync(path.join(dir, 'backup.json'), JSON.stringify({ created: new Date().toISOString(), entries }, null, 2) + '\n');
      }
    },
    entries,
    get dir() {
      return dir;
    },
  };
}

// ---------- args ----------

function parseArgs(argv) {
  const o = {
    command: null,
    hosts: [...ALL_HOSTS],
    copy: false,
    dryRun: false,
    yes: false,
    force: false,
    withDiagram: false,
    restore: false,
    help: false,
    version: false,
  };
  const bools = {
    '--copy': 'copy',
    '--dry-run': 'dryRun',
    '--yes': 'yes',
    '-y': 'yes',
    '--force': 'force',
    '--with-diagram-design': 'withDiagram',
    '--restore': 'restore',
    '--help': 'help',
    '-h': 'help',
    '--version': 'version',
    '-v': 'version',
  };
  for (let i = 0; i < argv.length; i++) {
    const raw = argv[i];
    let [flag, inline] = raw.startsWith('--') && raw.includes('=') ? [raw.slice(0, raw.indexOf('=')), raw.slice(raw.indexOf('=') + 1)] : [raw, undefined];
    if (flag === '--hosts') {
      const val = inline ?? argv[++i];
      if (!val) throw new UsageError('--hosts needs a value, e.g. --hosts claude,codex');
      const hosts = val.split(',').map((h) => h.trim().toLowerCase()).filter(Boolean);
      const bad = hosts.filter((h) => !ALL_HOSTS.includes(h));
      if (bad.length || !hosts.length) throw new UsageError(`unknown host: ${bad.join(', ') || val} (use ${ALL_HOSTS.join(', ')})`);
      o.hosts = [...new Set(hosts)];
    } else if (bools[flag] && inline === undefined) {
      o[bools[flag]] = true;
    } else if (flag.startsWith('-')) {
      throw new UsageError(`unknown flag: ${raw}`);
    } else if (!o.command) {
      if (!COMMANDS.includes(flag)) throw new UsageError(`unknown command: ${raw}`);
      o.command = flag;
    } else {
      throw new UsageError(`unexpected argument: ${raw}`);
    }
  }
  o.command ||= 'install';
  return o;
}

const hostDirKeys = (hosts) => [...new Set(hosts.flatMap((h) => HOST_KEYS[h]))];

// ---------- install ----------

function planInstall(ctx, o, names, gitOk) {
  const manifest = loadManifest(ctx);
  const owned = new Set(manifest.entries.map((e) => e.path));
  const keys = hostDirKeys(o.hosts);
  const mode = o.copy ? 'copy' : 'link';
  const items = [];
  const conflicts = [];
  const warnings = [];

  const targetOf = (name) => (name === DIAGRAM ? path.join(ctx.diagramDir, 'skills', DIAGRAM) : path.join(ctx.store, name));

  if (o.withDiagram && !gitOk && !resolves(path.join(targetOf(DIAGRAM), 'SKILL.md'))) {
    warnings.push(`git not found: skipping ${DIAGRAM}. project-report falls back to Mermaid diagrams.`);
    names = names.filter((n) => n !== DIAGRAM);
  }

  for (const key of keys) {
    for (const name of names) {
      const dest = path.join(ctx.hostDir[key], name);
      const target = targetOf(name);
      const st = lstat(dest);
      const item = { key, name, dest, target, mode };
      if (!st) {
        items.push({ ...item, op: 'create' });
        continue;
      }
      const ours = owned.has(dest) || (st.isSymbolicLink() && linkPointsTo(dest, target));
      if (ours) {
        const same = mode === 'link' && st.isSymbolicLink() && linkPointsTo(dest, target);
        items.push({ ...item, op: same ? 'keep' : 'replace-own' });
      } else if (st.isSymbolicLink()) {
        items.push({ ...item, op: 'replace-foreign-link' });
      } else if (o.force) {
        items.push({ ...item, op: 'replace-foreign-dir' });
      } else {
        conflicts.push(dest);
      }
    }
  }
  return { items, conflicts, warnings, names, targetOf };
}

function place(ctx, item, report) {
  fs.mkdirSync(path.dirname(item.dest), { recursive: true });
  if (item.mode === 'link') {
    try {
      fs.symlinkSync(item.target, item.dest, IS_WIN ? 'junction' : 'dir');
      return 'link';
    } catch (e) {
      report.warnings.push(`symlink failed for ${tilde(ctx, item.dest)} (${e.code || e.message}); copied instead`);
    }
  }
  copyTree(item.target, item.dest);
  return 'copy';
}

async function cmdInstall(ctx, o) {
  const dry = o.dryRun;
  let names = discoverSkills(SRC_SKILLS);
  if (!names.length) throw new Error(`no skills found in ${SRC_SKILLS}`);
  if (o.withDiagram) names = [...names, DIAGRAM];

  const plan = planInstall(ctx, o, names, o.withDiagram ? gitAvailable() : true);
  const report = { warnings: [...plan.warnings] };

  if (plan.conflicts.length) {
    console.error('Refusing to install: these folders already exist and are not links created by this tool:');
    for (const c of plan.conflicts) console.error(`  ${tilde(ctx, c)}`);
    console.error('Move them yourself, or re-run with --force to back them up to ~/.oh-my-writing/backup/ and replace them.');
    return 1;
  }

  const copyCount = names.filter((n) => n !== DIAGRAM).length;
  console.log(`Oh My Writing ${PKG.version}${dry ? ' (dry run, nothing will change)' : ''}`);
  console.log(`  copy ${copyCount} skills to ${tilde(ctx, ctx.store)}`);
  for (const key of hostDirKeys(o.hosts)) console.log(`  ${o.copy ? 'copy' : 'link'} into ${tilde(ctx, ctx.hostDir[key])}`);
  for (const i of plan.items.filter((x) => x.op === 'replace-foreign-link' || x.op === 'replace-foreign-dir')) {
    console.log(`  back up ${tilde(ctx, i.dest)} (not created by this tool)`);
  }

  if (!dry && !o.yes && process.stdin.isTTY) {
    if (!(await confirm('Proceed? [y/N] '))) {
      console.log('Cancelled. Nothing changed.');
      return 1;
    }
  }

  const backup = makeBackup(ctx, dry);
  const manifest = loadManifest(ctx);
  const linked = [];
  const copied = [];
  let kept = 0;
  let diagramReady = true;

  try {
    if (!dry) {
      fs.mkdirSync(ctx.store, { recursive: true });
      for (const name of names.filter((n) => n !== DIAGRAM)) {
        const dest = path.join(ctx.store, name);
        removePath(dest);
        copyTree(path.join(SRC_SKILLS, name), dest);
      }
      fs.writeFileSync(ctx.versionFile, PKG.version + '\n');
    }

    if (o.withDiagram) {
      const skillMd = path.join(plan.targetOf(DIAGRAM), 'SKILL.md');
      if (resolves(skillMd)) {
        console.log(`  ${DIAGRAM}: reusing ${tilde(ctx, ctx.diagramDir)}`);
      } else if (dry) {
        console.log(`  would run: git clone ${DIAGRAM_REPO} ${tilde(ctx, ctx.diagramDir)}`);
      } else if (lstat(ctx.diagramDir)) {
        report.warnings.push(`${tilde(ctx, ctx.diagramDir)} exists but has no skills/${DIAGRAM}/SKILL.md; skipped ${DIAGRAM}`);
        diagramReady = false;
      } else {
        const r = spawnSync('git', ['clone', '--depth', '1', DIAGRAM_REPO, ctx.diagramDir], { encoding: 'utf8' });
        if (r.status !== 0 || !resolves(skillMd)) {
          report.warnings.push(`git clone of ${DIAGRAM} failed (${(r.stderr || r.error?.message || 'unknown error').trim().split('\n').pop()}); skipped ${DIAGRAM}`);
          diagramReady = false;
        }
      }
    }

    for (const item of plan.items) {
      if (item.name === DIAGRAM && !diagramReady) continue;
      if (item.op === 'keep') {
        kept++;
        upsert(manifest, { path: item.dest, kind: 'link', skill: item.name, host: item.key, target: item.target });
        continue;
      }
      if (item.op === 'replace-foreign-link' || item.op === 'replace-foreign-dir') {
        backup.move(item.dest, `${item.key}-skills`);
      } else if (item.op === 'replace-own' && !dry) {
        removePath(item.dest);
      }
      let kind = item.mode;
      if (!dry) kind = place(ctx, item, report);
      (kind === 'link' ? linked : copied).push(item);
      if (!dry) upsert(manifest, { path: item.dest, kind, skill: item.name, host: item.key, target: item.target });
    }
  } finally {
    if (!dry) {
      manifest.version = PKG.version;
      manifest.installedAt = new Date().toISOString();
      manifest.backups = [...(manifest.backups || []), ...(backup.dir ? [{ dir: backup.dir, entries: backup.entries }] : [])];
      saveManifest(ctx, manifest);
    }
    backup.finish();
  }

  console.log('');
  console.log(dry ? 'Dry run summary (nothing was changed):' : 'Summary:');
  for (const key of hostDirKeys(o.hosts)) {
    const l = linked.filter((i) => i.key === key).length;
    const c = copied.filter((i) => i.key === key).length;
    const parts = [];
    if (l) parts.push(`${l} ${dry ? 'to link' : 'linked'}`);
    if (c) parts.push(`${c} ${dry ? 'to copy' : 'copied'}`);
    const keptHere = plan.items.filter((i) => i.key === key && i.op === 'keep').length;
    if (keptHere) parts.push(`${keptHere} already linked`);
    console.log(`  ${tilde(ctx, ctx.hostDir[key])}: ${parts.join(', ') || 'nothing'} (${hostsFor(o.hosts, key)})`);
  }
  if (backup.entries.length) {
    console.log(`  ${dry ? 'Would back up' : 'Backed up'} (moved, not deleted) to ${tilde(ctx, backup.dir)}:`);
    for (const e of backup.entries) console.log(`    ${tilde(ctx, e.original)}`);
  }
  for (const w of report.warnings) console.log(`  warning: ${w}`);
  console.log('');
  console.log('Verify:');
  console.log('  npx github:d41sys/oh-my-writing doctor');
  console.log(`  ls -l ${tilde(ctx, ctx.hostDir.agents)} ${tilde(ctx, ctx.hostDir.claude)} | grep oh-my-writing`);
  console.log('Then start a new Claude Code, Codex or omp session and ask: "Make this paragraph sound less like AI, keep every fact".');
  return 0;
}

const hostsFor = (hosts, key) => SEEN_BY[key].filter((h) => hosts.includes(h)).join(', ');

function upsert(manifest, entry) {
  manifest.entries = manifest.entries.filter((e) => e.path !== entry.path);
  manifest.entries.push(entry);
}

// ---------- uninstall ----------

function listBackups(ctx) {
  if (!fs.existsSync(ctx.backupRoot)) return [];
  return fs
    .readdirSync(ctx.backupRoot, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => ({ dir: path.join(ctx.backupRoot, d.name), name: d.name, meta: readJson(path.join(ctx.backupRoot, d.name, 'backup.json'), null) }))
    .filter((b) => b.meta && Array.isArray(b.meta.entries))
    .sort((a, b) => (a.name < b.name ? 1 : -1)); // newest first
}

function restoreBackups(ctx, dry) {
  const seen = new Set();
  const restored = [];
  const skipped = [];
  for (const b of listBackups(ctx)) {
    let remaining = 0;
    const left = [];
    for (const e of b.meta.entries) {
      const src = path.join(b.dir, e.backup);
      if (!lstat(src)) continue;
      if (seen.has(e.original)) {
        remaining++;
        left.push(e);
        continue;
      }
      seen.add(e.original);
      if (lstat(e.original)) {
        skipped.push(e.original);
        remaining++;
        left.push(e);
        continue;
      }
      if (!dry) moveRaw(src, e.original);
      restored.push(e.original);
    }
    if (!dry) {
      if (!remaining) fs.rmSync(b.dir, { recursive: true, force: true });
      else fs.writeFileSync(path.join(b.dir, 'backup.json'), JSON.stringify({ ...b.meta, entries: left }, null, 2) + '\n');
    }
  }
  return { restored, skipped };
}

async function cmdUninstall(ctx, o) {
  const dry = o.dryRun;
  const manifest = loadManifest(ctx);
  const removed = [];
  const left = [];

  console.log(`Oh My Writing uninstall${dry ? ' (dry run, nothing will change)' : ''}`);
  if (!manifest.entries.length && !o.restore) {
    console.log('Nothing to remove: no manifest entries in ' + tilde(ctx, ctx.manifestFile));
    return 0;
  }
  if (!dry && !o.yes && process.stdin.isTTY) {
    if (!(await confirm(`Remove ${manifest.entries.length} link/copy entries${o.restore ? ' and restore the backup' : ''}? [y/N] `))) {
      console.log('Cancelled. Nothing changed.');
      return 1;
    }
  }

  for (const e of manifest.entries) {
    const st = lstat(e.path);
    if (!st) continue;
    if (e.kind === 'link') {
      if (st.isSymbolicLink() && linkPointsTo(e.path, e.target)) {
        if (!dry) fs.unlinkSync(e.path);
        removed.push(e.path);
      } else left.push(`${e.path} (no longer the link this tool made)`);
    } else if (st.isDirectory() && !st.isSymbolicLink()) {
      if (!dry) fs.rmSync(e.path, { recursive: true, force: true });
      removed.push(e.path);
    } else left.push(`${e.path} (no longer the copy this tool made)`);
  }

  if (!dry) {
    removePath(ctx.store);
    removePath(ctx.versionFile);
    removePath(ctx.manifestFile);
  }

  let restore = { restored: [], skipped: [] };
  if (o.restore) restore = restoreBackups(ctx, dry);

  if (!dry) {
    for (const d of [ctx.backupRoot, ctx.root]) {
      try {
        fs.rmdirSync(d);
      } catch {
        /* not empty: backups or diagram-design remain */
      }
    }
  }

  console.log(`  ${dry ? 'Would remove' : 'Removed'} ${removed.length} link/copy entries:`);
  for (const p of removed) console.log(`    ${tilde(ctx, p)}`);
  for (const p of left) console.log(`  left in place: ${tilde(ctx, p)}`);
  if (o.restore) {
    console.log(`  ${dry ? 'Would restore' : 'Restored'} ${restore.restored.length} path(s) from backup:`);
    for (const p of restore.restored) console.log(`    ${tilde(ctx, p)}`);
    for (const p of restore.skipped) console.log(`  not restored, path already exists: ${tilde(ctx, p)}`);
    if (!restore.restored.length && !restore.skipped.length) console.log('    (no backups found)');
  } else if (listBackups(ctx).length) {
    console.log(`  Backups are kept in ${tilde(ctx, ctx.backupRoot)}. Add --restore to move the latest ones back.`);
  }
  if (fs.existsSync(ctx.diagramDir)) console.log(`  ${tilde(ctx, ctx.diagramDir)} was left in place; delete it yourself if you no longer want it.`);
  return 0;
}

// ---------- list / doctor ----------

function inspect(ctx) {
  const manifest = loadManifest(ctx);
  const owned = new Map(manifest.entries.map((e) => [e.path, e]));
  const names = [...new Set([...discoverSkills(SRC_SKILLS), ...manifest.entries.map((e) => e.skill)])].sort();
  const installed = readFileOr(ctx.versionFile);
  const rows = names.map((name) => {
    const states = {};
    for (const key of Object.keys(ctx.hostDir)) {
      const dest = path.join(ctx.hostDir[key], name);
      const st = lstat(dest);
      if (!st) states[key] = 'missing';
      else if (st.isSymbolicLink()) states[key] = resolves(dest) ? (owned.has(dest) ? 'linked' : 'linked-other') : 'broken';
      else states[key] = owned.has(dest) ? 'copy' : 'foreign';
    }
    return { name, states, seen: (h) => hostSees(states, h) };
  });
  return { manifest, rows, installed, names };
}

const readFileOr = (f) => {
  try {
    return fs.readFileSync(f, 'utf8').trim();
  } catch {
    return null;
  }
};
const present = (s) => s === 'linked' || s === 'linked-other' || s === 'copy' || s === 'foreign';
function hostSees(states, host) {
  const keys = host === 'claude' ? ['claude'] : host === 'codex' ? ['agents'] : ['agents', 'claude'];
  return keys.some((k) => present(states[k]));
}

function findPluginDuplicates(ctx, names) {
  const roots = [
    path.join(ctx.home, '.claude', 'plugins', 'cache'),
    path.join(ctx.home, '.claude', 'plugins', 'marketplaces'),
    path.join(ctx.home, '.codex', 'plugins', 'cache'),
  ];
  const wanted = new Set(names);
  const found = new Map();
  const walk = (dir, depth) => {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const d of entries) {
      if (!d.isDirectory() || d.name === 'node_modules' || d.name === '.git') continue;
      const p = path.join(dir, d.name);
      if (path.basename(dir) === 'skills' && wanted.has(d.name) && fs.existsSync(path.join(p, 'SKILL.md'))) {
        if (!found.has(d.name)) found.set(d.name, []);
        found.get(d.name).push(p);
      }
      if (depth < 7) walk(p, depth + 1);
    }
  };
  for (const r of roots) walk(r, 0);
  return found;
}

function cmdList(ctx, o, doctor) {
  const info = inspect(ctx);
  const installed = info.installed;
  console.log(`Oh My Writing: package ${PKG.version}, installed ${installed || 'not installed'} (store ${tilde(ctx, ctx.root)})`);
  console.log('');
  const w = Math.max(5, ...info.rows.map((r) => r.name.length));
  const cell = (r, h) => (hostBroken(r, h) ? 'BROKEN' : r.seen(h) ? 'yes' : '-');
  console.log(`${'skill'.padEnd(w)}  claude  codex   omp`);
  for (const r of info.rows) {
    console.log(`${r.name.padEnd(w)}  ${cell(r, 'claude').padEnd(6)}  ${cell(r, 'codex').padEnd(6)}  ${cell(r, 'omp')}`);
  }
  if (!doctor) return 0;

  const errors = [];
  const warns = [];
  if (!installed && !info.manifest.entries.length) errors.push('Not installed. Run: npx github:d41sys/oh-my-writing');
  if (installed && installed !== PKG.version) warns.push(`Installed ${installed}, this package is ${PKG.version}. Re-run install to update.`);

  for (const r of info.rows) {
    for (const key of Object.keys(ctx.hostDir)) {
      if (r.states[key] === 'broken') {
        const p = path.join(ctx.hostDir[key], r.name);
        let to = '?';
        try {
          to = fs.readlinkSync(p);
        } catch {
          /* ignore */
        }
        errors.push(`Broken link ${tilde(ctx, p)} -> ${to}. Re-run install, or remove the link.`);
      }
    }
  }

  for (const key of Object.keys(ctx.hostDir)) {
    const have = info.rows.filter((r) => present(r.states[key]));
    const missing = info.rows.filter((r) => r.states[key] === 'missing');
    if (have.length && missing.length) warns.push(`${tilde(ctx, ctx.hostDir[key])} lacks: ${missing.map((r) => r.name).join(', ')}`);
    for (const r of have.filter((x) => x.states[key] === 'foreign')) {
      warns.push(`${tilde(ctx, path.join(ctx.hostDir[key], r.name))} is a folder this tool did not create`);
    }
  }

  const dupes = findPluginDuplicates(ctx, info.names);
  for (const [name, paths] of dupes) {
    const inDirs = info.rows.find((r) => r.name === name && Object.values(r.states).some(present));
    if (inDirs) warns.push(`Duplicate skill ${name}: in the skill folders and in a plugin cache (${paths.map((p) => tilde(ctx, p)).join(', ')}). Two copies compete for routing; keep one.`);
  }

  console.log('');
  for (const e of errors) console.log(`error: ${e}`);
  for (const wn of warns) console.log(`warning: ${wn}`);
  console.log(`doctor: ${errors.length} error(s), ${warns.length} warning(s)`);
  return errors.length ? 1 : 0;
}

const hostBroken = (r, h) => (h === 'claude' ? ['claude'] : h === 'codex' ? ['agents'] : ['agents', 'claude']).some((k) => r.states[k] === 'broken');

// ---------- main ----------

async function main() {
  let o;
  try {
    o = parseArgs(process.argv.slice(2));
  } catch (e) {
    if (!(e instanceof UsageError)) throw e;
    console.error(`${e.message}\n\n${USAGE}`);
    return 2;
  }
  if (o.help) {
    console.log(USAGE);
    return 0;
  }
  if (o.version) {
    console.log(PKG.version);
    return 0;
  }
  const ctx = makeCtx();
  switch (o.command) {
    case 'install':
      return cmdInstall(ctx, o);
    case 'uninstall':
      return cmdUninstall(ctx, o);
    case 'list':
      return cmdList(ctx, o, false);
    case 'doctor':
      return cmdList(ctx, o, true);
  }
}

main().then(
  (code) => {
    process.exitCode = code;
  },
  (e) => {
    console.error(`oh-my-writing: ${e.message}`);
    process.exitCode = 1;
  },
);
