# Install Oh My Writing v2 (replaces the academic-writing install)

Oh My Writing v2 is the ten skills in `skills/`. They replace the old single `academic-writing` skill as your everyday writing setup. Claude Code, Codex and omp all load them from the same two folders.

Time: about 5 minutes.

## 1. Remove the old academic-writing install

The old install is a folder in `~/.agents/skills/` and a link in `~/.claude/skills/`. Move the folder aside instead of deleting it, so you can roll back:

```bash
mkdir -p ~/skills-backup
[ -L ~/.claude/skills/academic-writing ] && rm ~/.claude/skills/academic-writing
[ -e ~/.agents/skills/academic-writing ] && mv ~/.agents/skills/academic-writing ~/skills-backup/academic-writing
[ -L ~/.claude/commands/academic-writing.md ] && rm ~/.claude/commands/academic-writing.md
```

## 2. Get the code

```bash
git clone https://github.com/d41sys/academic-writing-skill.git ~/oh-my-writing
git -C ~/oh-my-writing checkout v2.0.0
```

## 3. Link the ten skills

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

**Plugin instead of links.** Claude Code: run `/plugin marketplace add d41sys/academic-writing-skill`, then `/plugin install oh-my-writing@oh-my-writing`. Codex can read `.codex-plugin/plugin.json`. Use either links or the plugin, not both: two copies of the same skill compete for routing.

## 4. Optional: diagrams for project-report

```bash
git clone https://github.com/cathrynlavery/diagram-design.git ~/diagram-design
ln -sfn ~/diagram-design/skills/diagram-design ~/.agents/skills/diagram-design
ln -sfn ~/diagram-design/skills/diagram-design ~/.claude/skills/diagram-design
```

Without it, `project-report` falls back to Mermaid diagrams.

## 5. Check it works

```bash
ls -l ~/.agents/skills ~/.claude/skills | grep oh-my-writing   # ten links in each
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

The skills never invent facts. Anything missing from your material comes back as `[ASK AUTHOR: …]` or `[VERIFY: …]`. Answer those, or remove them, before you send the text.

## Paper writing

v2 has no paper-section skill yet. The old paper workflow (story card, then outline, then draft, then external review) is still in this repository's root `SKILL.md`. To keep it beside v2, link it under its old name:

```bash
ln -sfn ~/oh-my-writing ~/.claude/skills/academic-writing
```

## Update and roll back

```bash
git -C ~/oh-my-writing fetch --tags && git -C ~/oh-my-writing checkout <new tag>   # update; the links stay valid
for s in ~/oh-my-writing/skills/*/; do rm -f ~/.agents/skills/$(basename "$s") ~/.claude/skills/$(basename "$s"); done
mv ~/skills-backup/academic-writing ~/.agents/skills/ && ln -s ../../.agents/skills/academic-writing ~/.claude/skills/academic-writing   # roll back
```

## Known limits (from the v2 benchmark)

Run on omp with gpt-6-sol, 3 repeats per case:

| Case set | With the skills | Without skills |
|---|---|---|
| Tuned cases | 89% | 42% |
| Held-out cases | 81% (17/21) | 57% |

- **Against seven other public writing-skill packs**, these skills passed more cases than every one of them.
- **The checks were written by the same team as the skills.** A blind model judge preferred the no-skill output about as often as the skill output, so the skills are more reliable on facts than clearly better-sounding.
- **On a weaker model the gap shrinks.** With gemini-3.8-flash, stock closers such as "Thank you for your time and consideration" and missing details came back.

Give a strong model these skills, and read every `[ASK AUTHOR]` marker in the output.
