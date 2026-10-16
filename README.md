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

## Slash command
```bash
mkdir -p ~/.claude/commands && ln -s ~/academic-writing-skill/commands/academic-writing.md ~/.claude/commands/academic-writing.md
```
Then: `/academic-writing rewrite the abstract` or `/academic-writing write the introduction, example paper: arXiv 2505.23941`.

## Oh My Writing skills

`skills/` holds ten general writing skills built from the Oh My Writing library below. They follow the [Agent Skills specification](https://agentskills.io/specification): each skill is `skills/<name>/SKILL.md` with on-demand `references/`, `assets/` templates, optional stdlib-only `scripts/`, a self-check `eval.md` run before returning output, and `agents/openai.yaml` for Codex. The academic-writing skill above stays at the repository root and is not part of the plugin.

| Skill | Use it to |
|---|---|
| `anti-slop-editing` | Detect or remove AI-writing patterns while preserving meaning, facts and the author's voice |
| `author-voice` | Build a voice profile from real samples, then draft or check text against it |
| `structured-drafting` | Turn notes and sources into a brief, outline and first draft, alone or section by section with the user |
| `evidence-grounded-writing` | Keep every claim at the strength its evidence supports: claims ledger, numbers, citations |
| `independent-review` | Review with a reader who lacks the writer's context; calibrate rubrics and triage findings |
| `post-writing` | Blog posts, essays, newsletters, social posts and repurposing |
| `report-writing` | Decision memos, research and market reports, executive summaries, post-mortems |
| `technical-docs` | Tutorials, how-to guides, reference, explanation, READMEs, PR descriptions, changelogs |
| `career-documents` | Truthful résumés, CVs, cover letters, statements of purpose, profiles and outreach |
| `project-report` | Turn a folder of project documents into a sourced, professional project report with designed diagrams, as one print-ready HTML file |

`project-report` draws its diagrams with the separate [diagram-design](https://github.com/cathrynlavery/diagram-design) skill when it is installed, and falls back to Mermaid blocks otherwise. Install it next to these skills:

```bash
git clone https://github.com/cathrynlavery/diagram-design.git ~/diagram-design
ln -s ~/diagram-design/skills/diagram-design ~/.agents/skills/diagram-design
ln -s ~/diagram-design/skills/diagram-design ~/.claude/skills/diagram-design
```

Install by linking the skill folders where each host looks for them. Claude Code reads `~/.claude/skills`; Codex reads `~/.agents/skills`; omp reads its own `~/.omp/agent/skills` and, with its Claude and Agents providers enabled (the default on this setup), the two folders above:

```bash
git clone git@github.com:d41sys/academic-writing-skill.git ~/academic-writing-skill
mkdir -p ~/.agents/skills ~/.claude/skills
for d in ~/academic-writing-skill/skills/*/; do
  ln -s "${d%/}" ~/.agents/skills/
  ln -s "${d%/}" ~/.claude/skills/
done
```

As a plugin: the repository root has `plugin.json` ([Agent Plugins](https://agent-plugins.org/) 1.0.0), `.codex-plugin/plugin.json` and `.claude-plugin/` (Claude Code: `/plugin marketplace add d41sys/academic-writing-skill`, then `/plugin install oh-my-writing@oh-my-writing`).

Validate and test:

```bash
for d in skills/*/; do uvx --from 'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref' skills-ref validate "$d"; done
uv run --with pytest --with pyyaml python -m pytest tests/_meta -q
for t in tests/*/; do [ -d "$t" ] && [ "$(basename "$t")" != _meta ] && uv run --with pytest python -m pytest "$t" -q; done
```

`tests/_meta` checks the shared contract for every skill: allowed frontmatter keys, quoted `metadata.version`, the license, the 500-line limit, `eval.md` and `agents/openai.yaml`, links that stay inside the skill, tests for any `scripts/`, and the absence of internal library IDs and source-repository names. Skill text is written in our own words; sources are thanked in Acknowledgments.

Benchmark: `evals/` runs realistic writing tasks on Codex and Claude Code with and without the skills and grades them mechanically (invented facts, lost negations and qualifiers, missing gap markers, leftover stock phrasing, leaked context), with an optional blind pairwise judge. `project-report` cases use real document folders in `evals/fixtures/` (docx, xlsx, pptx, pdf, eml, csv, md, with conflicts, superseded versions, noise and an embedded instruction), answer keys, diagram and HTML checks, repeated runs and a visual judge that scores page screenshots. `evals/review_pairs.py` builds a blind A/B page for rating the outputs yourself. See [evals/README.md](evals/README.md):

```bash
python3 evals/run.py --host codex --host claude --jobs 4
python3 evals/run.py --host codex --cases 'project-report/*' --repeat 3 --jobs 6 --judge codex
python3 evals/review_pairs.py evals/results/<run>
```

## License

MIT, see [LICENSE](LICENSE). Exception: Diátaxis-derived material, including `skills/technical-docs/`, stays CC-BY-SA 4.0 because that license requires adaptations to keep it. Third-party notices are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Oh My Writing: local knowledge and evaluation

Oh My Writing is an independently organized writing knowledge library, separate from the existing academic-writing runtime above. Start with [the subject index](references/knowledge/index.md), [coverage and limitations](references/knowledge-review.md), or the [research report](WRITING_RESEARCH_REPORT.md).

The [reference review report](REFERENCE_REVIEW_REPORT.md) records the current source-skill selection (§16), separately from the earlier synthesized-content usefulness audit (§14). Older source-fidelity tiers are historical, not approval of the expanded library.

The [review checklist](REVIEW_CHECKLIST.md) lists the human decisions still needed before the reference library is final.

For human review, open the generated `review/assets-review.html`. The main view selects **original writing skills and method libraries worth learning from**, not every repository file or internal K-ID. Common README/setup/configuration/release files and platform distributions are filtered with an exclusion ledger; a README containing the entire source prompt collection is an explicit exception. Retained skill instructions and supporting texts are read in full, including bounded parts for long files. Recommendations distinguish broad writing foundations, genre-specific value, redundancy, writing operations and unsuitable material. Each card explains value for our library, concrete overlap with named sources and what is already covered here. Suggestions remain model-assisted editorial opinions, not measured writing improvements. The full file inventory and earlier rewritten-content reviews are secondary tabs.

Rebuild the local review from completed assessment artifacts and cached sources:

```bash
node scripts/build-asset-source-index.mjs
node scripts/build-skill-scan.mjs
node scripts/prepare-skill-comparisons.mjs
node scripts/build-skill-value-review.mjs
node scripts/build-asset-review.mjs
open review/assets-review.html
```

These commands require local `review/usefulness-audit.json`, earlier provenance artifacts, `.cache/omw_sources/`, completed per-repo `review/skill-scan/*.assessment.json` and matching `comparison-results.json`. They do not download or re-judge source value. Full-text assessments and comparisons are separate evidence-backed review work, not a filename classifier hidden in the generators. Missing, changed or incomplete review inputs fail the build instead of generating placeholder suggestions. Source-source overlap is checked against retrieved candidate neighbors, not exhaustive all-pairs proof; candidate novelty is not proof that a method is absent from the whole library. Generated pages and audit data remain local artifacts. No reviewed knowledge file is imported, deleted or rewritten.

The final assembly also requires the completed semantic curation files `review/skill-scan/editorial-general.json`, `editorial-specialist.json` and `editorial-library-evidence.json`. The main review hides unrelated/no-writing-method groups and remaining common-role documents after reading; their assessments remain in `skill-value-audit.json` under `excludedAfterReading`. This avoids presenting GPU tools, privacy policies or evaluation fixtures as writing skills.

Decisions and notes stay in browser storage; export JSON to back them up. Skill decisions have their own record kind; older file and rewritten-content decisions remain intact. Matching counts and visible cards update with filters and decisions. “Mọi nhóm” removes only the group selection; “Xóa bộ lọc” clears all filter conditions and the group. Note editing preserves focus when the matching cards are unchanged. Content/assessment fingerprints prevent stale decisions from being treated as current approval.

The [conflicts register](CONFLICTS_REGISTER.md) lists every contradiction found between knowledge units, open or reconciled, so it can be reviewed later.

The [source insights report](SOURCE_INSIGHTS_REPORT.md) compares the 17 sources as skill designs: architecture, quality control, contradictions, and recommendations for this library.

The [source knowledge coverage report](KNOWLEDGE_COVERAGE_REPORT.md) compares retained, partial, and missing methods within explicit audit scopes. Its percentages are static checklist judgments, not whole-repository coverage or measured model performance.

References explain the writing methods directly: decisions, procedures, examples, exceptions, and checks. They do not send the model to copies of another repository. Shared guidance is merged by subject; specialist depth lives in our own modules. Load only what the task needs. The [100-pattern anti-slop catalog](references/ai-slop-catalog.md) and [post](references/writing-post.md), [paper](references/writing-paper.md), and [report](references/writing-report.md) guides supply detailed applications.

With Node.js 18+ and no npm dependencies:

```bash
# Retrieve complete decisions with their conditions and examples.
node scripts/get-reference.mjs --category evidence-and-claims --genre paper --query "negation exact numbers" --limit 3 --json

# Inspect cases and prepare a fresh model-visible workspace.
node scripts/writing-sandbox.mjs list
node scripts/writing-sandbox.mjs prepare --case case-02-paper-negation --out /tmp/omw-paper-run

# After a model writes response.json according to task.json:
node scripts/writing-sandbox.mjs evaluate --run /tmp/omw-paper-run --json
```

See [retrieval options](references/retrieval.md) and [sandbox protocol](references/sandbox.md). The same file/JSON interfaces can be used by omp, Codex, or Claude; no host-specific advisor is required. This does not install an automatic runner for those hosts.

The sandbox prepares workspaces and evaluates mechanical criteria. It does **not** enforce OS/network isolation, prove that self-reported references were read, or certify author voice and argument quality. Host permissions and observed telemetry must be supplied separately. The hand-authored sample responses exercise the harness; they are not model benchmark results.

## Acknowledgments

Thanks to the following projects and their contributors. Their work informed the writing knowledge that we merged, rewrote, reorganized, and extended. This is not a distribution of their skill packages, a claim of original authorship of all underlying ideas, or evidence that their benchmark results transfer to Oh My Writing.

| Project | Contribution we learned from |
|---|---|
| [Avoid AI Writing](https://github.com/conorbronsdon/avoid-ai-writing) | Context-sensitive editing, diagnostic patterns, preservation and no-op boundaries |
| [Humanizer](https://github.com/blader/humanizer) | Concrete writing tells, false positives and author voice |
| [Marketing Skills](https://github.com/coreyhaines31/marketingskills) | Audience research, positioning, copy, outreach, lifecycle and communications |
| [GreatWriter](https://github.com/d-wwei/great-writer) | Narrative, voice, adaptation and revision techniques |
| [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) | Article writing, comparison validity and evaluation methods |
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Scientific evidence, specialist reporting, review and visual communication |
| [AI Research Skills](https://github.com/Orchestra-Research/AI-Research-SKILLs) | ML/systems manuscripts, citations, evaluation and publication practice |
| [Anthropic Skills](https://github.com/anthropics/skills) | Collaborative drafting, fresh-reader review and skill evaluation |
| [Diátaxis](https://github.com/evildmp/diataxis-documentation-framework) | Reader-purpose distinctions and documentation construction |
| [STORM](https://github.com/stanford-oval/storm) | Perspective-driven inquiry and evidence-grounded synthesis |
| [Awesome AI Research Writing](https://github.com/Leey21/awesome-ai-research-writing) | Inspiration for bounded writing operations; no unlicensed original text is redistributed |
| [ARIS (Auto-claude-code-research-in-sleep)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Paper planning and drafting, claim and citation audits, review/rebuttal, figures, talks, grants and patent writing |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Writing-for-agents, draft shaping and interview-style clarification methods |
| [garden-skills](https://github.com/ConardLi/garden-skills) | Long-form article presentation and reader-facing layout |
| [ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills) | Résumé, CV, cover-letter, LinkedIn-profile and portfolio methods |
| [proficiently-claude-skills](https://github.com/proficientlyjobs/proficiently-claude-skills) | Truthful cover-letter and résumé tailoring |
| [jezweb/claude-skills](https://github.com/jezweb/claude-skills) | Award applications, proposals and regional business English |
| [diagram-design](https://github.com/cathrynlavery/diagram-design) | Diagram drawing for `project-report`; used as a separately installed skill, not bundled |
| University career and writing centers, DAAD, European Education Area | Statement-of-purpose, personal-statement and motivation-letter guidance (cited per unit) |

Copyright and license notices are preserved in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). In particular, the identified Diátaxis adaptations remain CC-BY-SA 4.0. Acknowledgment does not replace license compliance.

### Research and evaluation reading

Further background: [Agent Skills specification](https://agentskills.io/specification), [skill evaluation](https://agentskills.io/skill-creation/evaluating-skills), [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [agent evaluations](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), and the community site [claude.dev](https://claude.dev/). Community commentary is not an official product contract or measured result for this library.

### Foundational writing and detector reading

The earlier research also drew on these attributed reading leads, directly or through the projects above. They remain background reading, not mandatory reference-loading steps. Their empirical findings have not been independently reproduced by this library.

| Reading | Ideas acknowledged |
|---|---|
| George D. Gopen and Judith A. Swan, *The Science of Scientific Writing* | Reader expectations, topic/stress positions, and actions expressed through verbs |
| Zachary C. Lipton and Jacob Steinhardt, *Troubling Trends in Machine Learning Scholarship* | Explanation versus speculation, unnecessary formalism, and fair attribution of empirical gains |
| Roy Levin and David D. Redell, *How (and How Not) to Write a Good Systems Paper*; systems-writing guidance by Gernot Heiser and Irene Zhang | Originality, significance, verifiability, evaluation design, and thesis-driven abstracts |
| Wikipedia's AI Cleanup guidance; Charity Majors' *Confessions of an Unrepentant Sloper*; Simon Willison's *LLM Cliché Highlighter* | Formulaic rhetoric, stylistic homogenization, and contextual review of lexical signals |
| Liang and colleagues' 2023 detector-bias research; Jabarian and Imas' 2025 detector research | False-positive risks and the limits of inferring authorship from classifier outputs |

Platform-ranking descriptions, including discussion of `xai-org/x-algorithm` in the surveyed marketing material, are research leads rather than verified current platform rules. No ranking weights or engagement outcomes are assumed by the writing references.

### Publisher guideline sources

The local [publisher export profiles](references/knowledge/visuals-and-formatting/publisher-export-profiles.md) contain the substantive planning knowledge. These primary URLs support attribution and future maintenance, not mandatory online reference loading. Dates describe the inherited source snapshots, not fresh verification by this project.

| Publisher scope | Primary instructions and snapshot boundary |
|---|---|
| Nature flagship | [Final submission](https://www.nature.com/nature/for-authors/final-submission) and [figure specifications](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications), source review 2026-10-01; not portfolio-wide. |
| Science flagship | [Initial](https://www.science.org/content/page/instructions-preparing-initial-manuscript) and [revised](https://www.science.org/content/page/instructions-preparing-revised-manuscript) instructions, historical 2026-07-23 snapshot; fresh access was blocked in the 2026-10-01 source review. |
| Cell Press | [Figure guidelines](https://www.cell.com/information-for-authors/figure-guidelines), source review 2026-10-01; journal and article-type exceptions apply. |
| PLOS | [PLOS Computational Biology figures](https://journals.plos.org/ploscompbiol/s/figures), source review 2026-10-01; verify the selected journal. |
| Elsevier | [Formats checklist](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist) and [artwork sizing](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing), source review 2026-10-01; journal instructions override general defaults. |
| IEEE journals | [Resolution and size](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/), page modified 2025-02-25, source review 2026-10-01. |
| BMC Bioinformatics | [Submission guidelines](https://link.springer.com/journal/12859/submission-guidelines), source review 2026-10-01; one journal example, not a BMC-wide guarantee. |
| ACS | [Legacy manuscript graphics](https://pubsapp.acs.org/paragonplus/submission/general/graphics_prep.html), updated 2006-01-21; not a current universal digital-export standard. |
