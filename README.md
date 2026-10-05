# academic-writing

A Claude Code skill that writes ML/CV/NLP paper sections (one part at a time, or a whole paper) from your results and notes, with checking built in:

1. **Story card** (`paper/STORY.md`) approved by you before any prose.
2. **Outline** as `% TL;DR` comments, one per paragraph, each naming its source.
3. **Draft** under the outline.
4. **Check**: self-check (fact trace, story trace, AI-wording scans, section rules), then an **external review by a different model** (Codex CLI, fresh read-only session per round, at most two rounds).
5. **Hand-off**: the drafted part plus a short list of items for you to approve.

Optional: give an example paper and the skill writes `paper/EXEMPLAR_NOTES.md`, an analysis of its research design (question, design lever, argument chain, benchmark construction, claims vs evidence) and what transfers to your paper.

Project-specific review lessons go in `paper/WRITING_LESSONS.md` in each project; the skill applies them if present.

## Install (global)
```bash
git clone git@github.com:d41sys/academic-writing-skill.git ~/academic-writing-skill
ln -s ~/academic-writing-skill ~/.claude/skills/academic-writing
```
Update: `git -C ~/academic-writing-skill pull`.

## Use
"Rewrite the abstract", "write the introduction", or "write the paper". Works alongside the ARIS research skills (`paper-plan`, `paper-claim-audit`, `citation-audit`).

## Test the scans
`tests/scan_fixture.tex` is a positive control for the Tier-1/Tier-2 scans in `references/ai-tells.md`: Tier 1 must hit lines 2, 4, 12 only; Tier 2 must flag only paragraph 3.
