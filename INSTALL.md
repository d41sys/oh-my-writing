# Install Oh My Writing v2

Oh My Writing v2 is the eleven skills in `skills/`. Claude Code, Codex and omp all load them from the same two folders.

Time: about 1 minute with npx, about 5 minutes by hand.

## Install with npx

Needs Node 18 or newer and git.

```bash
npx github:d41sys/oh-my-writing
```

Copies the eleven skills to `~/.oh-my-writing/skills/` and links them into `~/.agents/skills` (Codex, omp) and `~/.claude/skills` (Claude Code, omp). If published to npm later, `npx oh-my-writing` does the same.

Flags (add them after the command, for example `npx github:d41sys/oh-my-writing install --dry-run`):

| Flag | Effect |
|---|---|
| `--dry-run` | Print what would happen, change nothing |
| `--yes` | Skip the confirmation prompt |
| `--hosts claude,codex,omp` | Install for these hosts only (default: all) |
| `--copy` | Copy into the host folders instead of symlinking |
| `--force` | Back up and replace an existing folder that has a skill's name (without it, the install stops) |
| `--with-diagram-design` | Also `git clone` [diagram-design](https://github.com/cathrynlavery/diagram-design) into `~/.oh-my-writing/diagram-design` and link it |

Check, uninstall, roll back:

```bash
npx github:d41sys/oh-my-writing doctor                    # versions, hosts, broken links, duplicates
npx github:d41sys/oh-my-writing list                      # which host sees which skill
npx github:d41sys/oh-my-writing uninstall                 # removes only the links/copies it made
npx github:d41sys/oh-my-writing uninstall --restore       # same, then moves folders that --force backed up back
```

`uninstall` tracks its own entries in `~/.oh-my-writing/manifest.json`. A folder you put in place of one of its links is left alone.

## Manual install

Use this if you do not want npx. Same result as above.

### 1. Get the code

```bash
git clone https://github.com/d41sys/oh-my-writing.git ~/oh-my-writing
git -C ~/oh-my-writing checkout v2.3.0
```

### 2. Link the eleven skills

```bash
mkdir -p ~/.agents/skills ~/.claude/skills
for d in ~/oh-my-writing/skills/*/; do
  ln -sfn "${d%/}" ~/.agents/skills/
  ln -sfn "${d%/}" ~/.claude/skills/
done
```

Where each host reads:

| Host | Folder |
|---|---|
| Claude Code | `~/.claude/skills` |
| Codex | `~/.agents/skills` |
| omp | both of the above, when its Claude and Agents skill providers are on (the default) |

**Plugin instead of links.** Claude Code: run `/plugin marketplace add d41sys/oh-my-writing`, then `/plugin install oh-my-writing@oh-my-writing`. Codex can read `.codex-plugin/plugin.json`. Use either links or the plugin, not both: two copies of the same skill compete for routing.

### 3. Optional: diagrams for project-report

```bash
git clone https://github.com/cathrynlavery/diagram-design.git ~/diagram-design
ln -sfn ~/diagram-design/skills/diagram-design ~/.agents/skills/diagram-design
ln -sfn ~/diagram-design/skills/diagram-design ~/.claude/skills/diagram-design
```

Without it, `project-report` falls back to Mermaid diagrams.

### 4. Check it works

```bash
ls -l ~/.agents/skills ~/.claude/skills | grep oh-my-writing   # eleven links in each
```

Then, in a new session of Claude Code, Codex or omp, ask: `Make this paragraph sound less like AI, keep every fact` and paste a paragraph. The reply should come from `anti-slop-editing`. In omp, the skill read shows as `skill://anti-slop-editing`.

## What to ask for

| You want | Ask like this | Skill that answers |
|---|---|---|
| Remove AI tone, keep facts | "edit this so it doesn't read like AI" | anti-slop-editing |
| Write like you | "here are 3 of my posts, write this in my voice" | author-voice |
| Notes to a draft | "turn these notes into a draft" | structured-drafting |
| Check claims and numbers | "fact-check this", "tone down the overclaiming" | evidence-grounded-writing |
| A second opinion | "review this as a reader who wasn't here" | independent-review |
| Posts | blog, LinkedIn, X thread, newsletter, launch post | post-writing |
| Reports | decision memo, exec summary, post-mortem, vendor comparison | report-writing |
| Docs | README, tutorial, PR description, changelog, ADR | technical-docs |
| Career | résumé, cover letter, statement of purpose, cold email | career-documents |
| Folder to report | "make a project report from these documents" | project-report |
| Result charts | "plot these results for the paper", "make the confusion matrices" | results-visualization |

The skills never invent facts. Anything missing from your material comes back as `[ASK AUTHOR: …]` or `[VERIFY: …]`. Answer those, or remove them, before you send the text.

## Update and remove

```bash
git -C ~/oh-my-writing fetch --tags && git -C ~/oh-my-writing checkout <new tag>   # update; the links stay valid
for s in ~/oh-my-writing/skills/*/; do rm -f ~/.agents/skills/$(basename "$s") ~/.claude/skills/$(basename "$s"); done   # remove the links
```

## Known limits (from the benchmark)

Measured on omp with gpt-6-sol, 3 repeats per case, on the commit just before the last two skill edits in v2 (generic routing descriptions and reworded source passages). The current version has not been re-run in full. Details: [docs/BENCHMARK.md](docs/BENCHMARK.md).

| Case set | With the skills | Without skills |
|---|---|---|
| Tuned cases | 89% | 42% |
| Held-out set 1 | 81% (17/21) | 57% |

- **Against seven other public writing-skill packs**, these skills passed more cases than every one of them.
- **The checks were written by the same team as the skills.** A blind model judge preferred the no-skill output about as often as the skill output, so the skills are more reliable on facts than clearly better-sounding.
- **On a weaker model the gap shrinks.** With gemini-3.8-flash, stock closers such as "Thank you for your time and consideration" and missing details came back.

Give a strong model these skills, and read every `[ASK AUTHOR]` marker in the output.
