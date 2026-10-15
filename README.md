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

## Oh My Writing: local knowledge and evaluation

Oh My Writing is an independently organized writing knowledge library, separate from the existing academic-writing runtime above. Start with [the subject index](references/knowledge/index.md), [coverage and limitations](references/knowledge-review.md), or the [research report](WRITING_RESEARCH_REPORT.md).

The [reference review report](REFERENCE_REVIEW_REPORT.md) includes a usefulness-first assessment (§14). Older source-fidelity tiers are historical, not an approval of the expanded library.

The [review checklist](REVIEW_CHECKLIST.md) lists the human decisions still needed before the reference library is final.

For human review, open the generated `review/assets-review.html`. It defaults to **original assets by repository**, identified by their original paths—not by K-IDs. K-IDs identify our rewritten knowledge, available separately in the **synthesized methods** and **rewritten knowledge groups** tabs. The five keep / conditional / consolidate / runtime / exclude recommendations assess synthesized entries, not complete original files. Source files without a usefulness assessment are labelled explicitly. Your decisions and notes stay in browser storage; export JSON to back them up. The page does not modify library files.

Rebuild the local review from the existing audit JSON and cached sources:

```bash
node scripts/build-asset-source-index.mjs
node scripts/build-asset-review.mjs
open review/assets-review.html
```

These commands require local `review/usefulness-audit.json`, the earlier review/provenance artifacts and `.cache/omw_sources/`; they do not download or re-evaluate sources. The generated page and data are local artifacts, not committed assets. Source links attached to a unit establish association, not exact provenance for every restored sentence. Files not usefulness-reviewed are labelled separately from the five recommendations.

The active tab, group chips and results summary show matching counts, not fixed catalogue totals. Changing a source filter clears the selected source group to avoid a hidden intersection with a different repo. “Mọi nhóm” removes only the group selection; “Xóa bộ lọc” clears the group and all filter conditions. Review-state filters update the visible cards immediately when a decision changes; note editing keeps focus when the matching cards are unchanged.

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
