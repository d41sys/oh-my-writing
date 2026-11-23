# Oh My Writing

Writing skills for AI agents that draft and edit **without AI slop, invented facts, or a flattened author voice**. Eleven [Agent Skills](https://agentskills.io/specification) for Claude Code, Codex and omp: anti-slop editing, author voice, drafting from notes, evidence checks, independent review, posts, reports, technical docs, career documents, project reports with designed diagrams, and result charts for papers.

```bash
npx github:d41sys/oh-my-writing
```

The installer links the skills for every host and backs up the old `academic-writing` skill. Manual install, plugin install and uninstall are in [INSTALL.md](INSTALL.md).

## Skills

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
| `project-report` | Turn a folder of project documents into a sourced, professional project report with designed diagrams, as one print-ready HTML file plus a Markdown copy that reads on its own |
| `results-visualization` | Plot experiment results as paper-ready charts in one consistent style, read from the result files |

Ask in plain words, for example "edit this so it doesn't read like AI, keep every fact" or "make a project report from these documents". The matching skill loads on its own. Anything missing from your material comes back as `[ASK AUTHOR: …]` or `[VERIFY: …]`, never as a guess.

**Usage guide:** [docs/USAGE.md](docs/USAGE.md) covers what to ask, what you get, combining skills, the helper scripts and troubleshooting.

## Benchmark

94 realistic writing tasks, 3 runs each, omp with gpt-6-sol (run `v-final4-omp`; one case was removed from the repository after the run). Details, judge results and limits: [docs/BENCHMARK.md](docs/BENCHMARK.md).

| Case group | With skills | No skills |
|---|---|---|
| Tuned (183 runs) | **70%** | 32% |
| Held-out 1 (33 runs) | 48% | 45% |
| Held-out 2 and later (66 runs) | 91% | 82% |
| All (282 runs) | **73%** | 45% |

The checks measure faithfulness: invented facts, lost hedges and negations, missing gap markers, stock phrasing. Most of the gain is on the cases the skills were tuned on; on held-out cases it is small. A blind judge preferred the no-skills output 111 to 69. Three skills make most of that gap (independent-review, project-report, report-writing); on the other cases the judge split 54 to 46 for the skills.

Against seven public writing-skill packs, on an earlier commit (run `v-final2-omp`):

| Pack | Ours passed | Theirs passed | Runs |
|---|---|---|---|
| avoid-ai-writing | **37** | 21 | 42 |
| humanizer | **37** | 17 | 42 |
| great-writer | **35** | 17 | 39 |
| doc-coauthoring | **22** | 18 | 24 |
| marketing copywriting | **18** | 12 | 21 |
| proficiently cover letter | **15** | 8 | 15 |
| ResumeSkills | **15** | 9 | 15 |

The blind judge preferred our output to every pack except humanizer.

A pre-registered run with a placebo (each skill's name and layout with generic advice of the same length) on the four skills revised last: 74% passed with our skills, 29% with the placebo, 38% with no skills. The blind judge did not agree. It preferred the placebo 34 to 27, mostly on independent-review, so we do not claim the judge sees the gain. See [Placebo control](docs/BENCHMARK.md#placebo-control-pre-registered).

**Tests:** about 850 unit tests cover the skill contract, every helper script, the grader and the installer. Run `for t in tests/*/; do uv run --with pytest --with pyyaml --with numpy --with matplotlib python -m pytest "$t" -q; done`.

## Site

The project site lives in `site/` (Vite, vanilla JS). It is separate from the installer above and is not published to npm.

Developing the website needs Node 20.19.x or Node 22.12 and newer. Installing the writing skills themselves still works on Node 18.

```bash
cd site
npm install
npm run dev      # local dev server
npm run build    # static files in site/dist, relative asset paths
npm run preview  # serve site/dist locally
```

## Contributing

Bug reports with a real failing example, new benchmark cases and rule fixes are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, skill rules (your own wording, general rules not test fixes, no invented facts) and how to add a case.

## License

MIT, see [LICENSE](LICENSE). Exception: Diátaxis-derived material, including `skills/technical-docs/`, is adapted from Diátaxis and stays CC-BY-SA 4.0. Notices are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Acknowledgments

Oh My Writing was inspired by these open-source projects, which we used as references while writing our own skills: Avoid AI Writing, Humanizer, Marketing Skills, GreatWriter, Everything Claude Code, Scientific Agent Skills, AI Research Skills, Anthropic Skills, Diátaxis, STORM, Awesome AI Research Writing, ARIS, mattpocock/skills, garden-skills, ResumeSkills, proficiently-claude-skills and jezweb/claude-skills. The skills are our own work and wording ([similarity check](docs/SOURCE_SIMILARITY.md)). project-report draws its diagrams with [diagram-design](https://github.com/cathrynlavery/diagram-design), installed separately and not bundled. Copyright and license notices are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); Diátaxis-derived material, including `skills/technical-docs/`, is adapted and stays CC-BY-SA 4.0.

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

## Paper writing: academic-writing (legacy)

The repository root still holds the original `academic-writing` skill for ML/CV/NLP paper sections. It is not part of v2 and not installed by default. To use it beside v2: `ln -sfn ~/oh-my-writing ~/.claude/skills/academic-writing`.


A Claude Code skill that writes ML/CV/NLP paper sections (one part at a time, or a whole paper) from your results and notes, with checking built in:

1. **Story card** (`paper/STORY.md`) approved by you before any prose.
2. **Outline** as `% TL;DR` comments, one per paragraph, each naming its source.
3. **Draft** under the outline.
4. **Check**: self-check (fact trace, story trace, AI-wording scans, section rules), then an **external review by a different model** (Codex CLI, fresh read-only session per round, at most two rounds).
5. **Hand-off**: the drafted part plus a short list of items for you to approve.

Optional: give an example paper and the skill writes `paper/EXEMPLAR_NOTES.md`, an analysis of its research design (question, design lever, argument chain, benchmark construction, claims vs evidence) and what transfers to your paper.

Project-specific review lessons go in `paper/WRITING_LESSONS.md` in each project; the skill applies them if present.

### Install (global)
```bash
git clone https://github.com/d41sys/oh-my-writing.git ~/oh-my-writing
ln -s ~/oh-my-writing ~/.claude/skills/academic-writing
```
Update: `git -C ~/oh-my-writing pull`.

### Use
"Rewrite the abstract", "write the introduction", or "write the paper". Works alongside the ARIS research skills (`paper-plan`, `paper-claim-audit`, `citation-audit`).

### Test the scans
`tests/scan_fixture.tex` is a positive control for the Tier-1/Tier-2 scans in `references/ai-tells.md`: Tier 1 must hit lines 2, 4, 12 only; Tier 2 must flag only paragraph 3.

### Slash command
```bash
mkdir -p ~/.claude/commands && ln -s ~/oh-my-writing/commands/academic-writing.md ~/.claude/commands/academic-writing.md
```
Then: `/academic-writing rewrite the abstract` or `/academic-writing write the introduction, example paper: arXiv 2505.23941`.
