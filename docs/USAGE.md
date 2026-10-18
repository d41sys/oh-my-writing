# Using Oh My Writing

Ten skills that load on their own when your request matches them. You do not name a skill or run a command. Ask in plain words, and give the agent your material: notes, files, drafts, samples. This guide covers what to ask, what you get back, and how to combine skills.

- [How the skills behave](#how-the-skills-behave)
- [Skill by skill](#skill-by-skill)
- [Combining skills](#combining-skills)
- [The helper scripts](#the-helper-scripts)
- [Getting good results](#getting-good-results)
- [Troubleshooting](#troubleshooting)

## How the skills behave

Every skill follows four rules:

1. **Nothing is invented.** Numbers, names, dates, quotes, results, anecdotes, links and calls to action come only from your material.
2. **Gaps come back as markers**, never as guesses:

   | Marker | Meaning | What you do |
   |---|---|---|
   | `[ASK AUTHOR: …]` | Only you know this, for example a missing date, an owner, or which of two figures is right | Answer it or delete the sentence |
   | `[VERIFY: …]` | A claim that needs a source check (health, legal, finance, statistics) | Check it before publishing |
   | `[UNTESTED]` | Code or a command nobody ran | Run it or keep the label |

   Markers sit outside the reader-facing text: in the reply, or in an `open-questions.md` file. Clear them before you send anything.
3. **Your meaning stays.** Edits keep negations, hedges ("may", "in one site"), scope and figures exactly. `anti-slop-editing` checks this with a script.
4. **Self-check before returning.** Each skill runs its `eval.md` checklist on the output before it answers.

## Skill by skill

### anti-slop-editing: make text stop reading like AI

- **Ask:** "edit this so it doesn't read like AI", "find the AI tells in this, don't change it", "clean this up but keep every fact".
- **Give:** the text, where it will appear (blog, report, README, chat), any passages that must not change, and a sample of your own writing if you have one.
- **Modes:** *detect* (a report of what reads as machine-written, with no edits) or *edit* (a revised text plus a list of changes).
- **You get:** the text with stock phrasing, filler, staged reveals and uniform rhythm removed. If the text is already fine, it says so and changes nothing.
- **Checks:** `slop_scan.py` lists remaining patterns. `fact_diff.py` lists any number, negation, name or hedge that was lost or added.

### author-voice: write like you

- **Ask:** "here are three of my posts, build my voice profile", "write this update in my voice", "does this draft sound like me?"
- **Give:** 3 or more real samples of your writing, each 150 words or more. One sample works, but the profile is marked low-confidence.
- **Modes:**
  - *build*: a voice profile listing person, sentence length, contractions, openers and the things you never do;
  - *apply*: draft in that voice;
  - *check*: compare a draft with the profile.
- **You get:** a profile file you can reuse, or a draft that keeps your habits. Biography or opinions you never wrote are never added.

### structured-drafting: from notes to a draft

- **Ask:** "turn these notes into a draft", "outline this for me", "help me write this together, section by section".
- **Give:** notes, transcripts, meeting notes, source excerpts or a rough draft, plus who will read it.
- **You get:** a draft. On bigger jobs you get a brief, an outline and then the draft. The stages scale with the size: a three-line email skips them. In co-authoring mode it stops after each section for your input.
- **Rule:** contradictions in your material, such as two different figures for the same thing, are shown and asked about. It never picks one for you.

### evidence-grounded-writing: claims that match the evidence

- **Ask:** "fact-check this", "tone down the overclaiming", "audit the citations", "are these numbers right?", "build a claims ledger".
- **Modes:**
  - *audit*: a ledger plus findings;
  - *write from sources*;
  - *edit guard*: rejects edits that strengthen claims;
  - *synthesis*: where the sources agree, where they conflict, and what is missing.
- **You get:** a claims ledger with these columns: claim, evidence location, status, action. Each claim is rewritten at the strength its evidence supports: correlation is not causation, and one site is not every site.

### independent-review: a second reader without your context

- **Ask:** "review this as someone who wasn't in the meetings", "write a reviewer prompt for another model", "triage these review comments".
- **You get:** findings with severity, the exact quote, and the consequence for the reader. Or you get a ready-to-paste prompt for a separate reviewer model, with a `VERDICT:` line to parse.
- **Rule:** when the same session wrote the text and reviews it, it says so. It does not call that review independent.

### post-writing: posts and articles

- **Ask:** blog post, essay, newsletter, LinkedIn post, X thread, launch announcement, onboarding emails, "turn this article into a thread".
- **Give:** the material, the platform, the audience, and any post of yours to match.
- **You get:** a post that opens on something concrete and puts proof ahead of adjectives. It has no invented story, customer or metric. If you asked for a story and gave none, it asks for one.

### report-writing: memos and reports

- **Ask:** decision memo, executive summary, research or market report, vendor comparison, post-mortem.
- **You get:** the conclusion first, with comparisons only on like-for-like terms. If the material makes no recommendation, the report says so and does not invent one. Post-mortems are blameless.

### technical-docs: documentation

- **Ask:** README, tutorial, how-to, API or CLI reference, architecture explanation, PR description, commit message, changelog, release notes, migration guide, ADR.
- **You get:** the page type that fits what the reader needs: learn, do, look up or understand. Commands and results it did not run are marked `[UNTESTED]`.

### career-documents: true and tailored

- **Ask:** résumé, CV, cover letter, statement of purpose, LinkedIn profile, cold email to a professor or hiring manager.
- **Give:** your background (CV, notes) and the target (job ad, program page).
- **You get:** a document tailored to the target with nothing inflated. A skill you lack is not claimed, and missing metrics are asked for, not made up.

### project-report: a folder of documents to a report

- **Ask:** "make a project report from these documents", "status report from this folder".
- **Give:** a folder of documents: docx, xlsx, pptx, pdf, eml, csv or md.
- **You get:**
  - one print-ready HTML file with designed diagrams, and a Markdown copy;
  - a fact ledger tracing every figure to its file;
  - an `open-questions.md`.
- **Rule:** conflicting figures across files stay visible, and superseded versions are flagged.
- **Diagrams** use [diagram-design](https://github.com/cathrynlavery/diagram-design) when it is installed, otherwise Mermaid. Install it with `npx github:d41sys/academic-writing-skill install --with-diagram-design`.

## Combining skills

The agent often loads more than one skill. You can also ask for a combination directly:

| Goal | Ask | Skills used |
|---|---|---|
| A LinkedIn post in your voice | "write this as a LinkedIn post in my voice; samples attached" | post-writing + author-voice |
| A report you can defend | "write the memo, then fact-check it against the data" | report-writing + evidence-grounded-writing |
| Draft, then a second opinion | "draft it, then review it as an outside reader" | structured-drafting + independent-review |
| De-AI an essay without losing claims | "make this sound human, don't change any claim" | anti-slop-editing + evidence-grounded-writing |

## The helper scripts

The skills run these scripts themselves. You can also run them directly. They use only the Python 3 standard library.

```bash
S=~/.oh-my-writing/skills   # or wherever the skills are installed
python3 $S/anti-slop-editing/scripts/slop_scan.py --profile professional draft.md
python3 $S/anti-slop-editing/scripts/fact_diff.py before.md after.md   # what changed in facts
python3 $S/author-voice/scripts/voice_stats.py sample1.md sample2.md sample3.md
python3 $S/evidence-grounded-writing/scripts/claim_ledger.py report.md  # sentences that need evidence
python3 $S/project-report/scripts/inventory.py --out work/ docs/       # inventory a document folder
```

## Getting good results

1. **Give material, not topics.** "Write about our migration" gets questions back. "Here are the notes, the budget sheet and the status emails" gets a draft.
2. **Name the reader and the place**, for example "for the steering group, sent by email" or "for a public LinkedIn post".
3. **Mark what must not change:** a quote, a legal sentence, a figure.
4. **Give writing samples** whenever voice matters.
5. **Answer the markers.** They are the agent telling you exactly what it does not know.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| No skill seems to load | Start a new session after installing. Run `npx github:d41sys/academic-writing-skill doctor` to see which hosts see which skills. |
| The old academic-writing skill answers | It is still installed. Run the installer again (it backs up the old skill) or remove it by hand: see [INSTALL.md](../INSTALL.md). |
| Two copies of a skill | Use either the plugin or the installer links, not both. `doctor` warns about duplicates. |
| The output still has stock closers or filler | Weaker models follow the rules less reliably. Ask again with "check it against anti-slop-editing", or use a stronger model. |
| Too many markers | Your material is missing facts the text needs. Add them, or tell the agent to leave those sentences out. |
