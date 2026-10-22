---
name: career-documents
description: "Writes and edits truthful career documents from the candidate's real material: résumés, academic CVs, tailoring to a job posting, cover letters, statements of purpose, personal statements, motivation letters, LinkedIn and portfolio profiles, short application-form answers, and cold, networking, warm-intro, thank-you or prospective-supervisor emails. Never invents experience, dates, titles, skills, contacts or numbers. Use when the user asks to write, rewrite, tailor, shorten or review a resume, CV, cover letter, SOP, personal statement, motivation letter, LinkedIn headline or About section, application answer, or a job-search, networking or academic outreach email."
license: MIT
metadata:
  version: "1.5"
  skill-author: d41sys
---

# Career Documents

Career writing is a selection problem under a truth constraint. The candidate's real record is the only raw material. The job is to choose which true facts to show, put them in the order the reader needs, and word them plainly. Nothing is added that the candidate did not supply or confirm.

This skill covers résumés and CVs, tailoring, cover letters, statements, profiles, short application answers and outreach. It works on its own. Sibling skills help when installed and are optional.

## When to use

- Build, refresh, shorten or review a résumé or academic CV.
- Tailor a résumé or letter to a specific job posting.
- Write a cover letter, statement of purpose, personal statement, motivation letter, or scholarship or award essay.
- Write a LinkedIn headline, About section, experience entries, portfolio case study, or a reusable story bank.
- Answer short application-form fields ("why us", "years with X", "tell us about yourself").
- Draft a cold email, networking message, referral or warm-intro request, thank-you note, reference request, offer reply, or an email to a prospective supervisor or program contact.

Not for: ML paper sections (use `academic-writing` if installed; otherwise `structured-drafting` for structure plus `evidence-grounded-writing` for claims); blog posts, essays, newsletters, email sequences and LinkedIn feed posts (use `post-writing`); research, market or decision reports (use `report-writing`); READMEs and PR text (use `technical-docs`); building a voice profile from samples (use `author-voice`). Investor, customer, partner or sales outreach (cold emails, pitches, sales follow-ups) is out of scope for all of the writing skills here; this skill covers outreach for jobs, careers and academia only.

## Inputs

Read before writing, in this order of authority:

1. The candidate's own material: current résumé or CV, profile export, notes, past letters, project lists. This is the only source of facts.
2. The target: the full posting, the program prompt and word limit, the form field labels, or the recipient's public page. If the target is a link that cannot be read, ask the user to paste the text.
3. The governing instructions: whatever the employer, program, portal or agency says about length, file type, structure and required items. These outrank every default in this skill. Tell the user to confirm the current version, because instructions change.

Ask at most three questions, fewer for short tasks, and only when the answer changes the output. Typical ones: which posting or prompt this is for; which country or field the reader is in (conventions differ); a number or scope detail that is missing from a strong accomplishment. Otherwise (and always in non-interactive runs) proceed and list assumptions at the end.

For a thin source, use [evidence inventory template](assets/evidence-inventory-template.md) to run a short interview first. If the user will paste text into a hosted tool, suggest leaving out ID numbers, home address, birth date and similar personal data, and swapping in stand-in values for those fields only (the final document uses the real ones).

## Workflow

Modes: **build** (new or refreshed master), **tailor** (one target), **letter** (cover letter, statement, award essay), **profile** (LinkedIn, portfolio, short answers), **outreach** (cold, networking, academic, warm intros, thank-yous, references, offers). Steps 1 to 4 apply to every mode.

1. **Fix the truth boundary.** List what the candidate supplied. Anything not on that list is unknown, not available for use. A missing detail is left out, or the sentence is kept at the level the facts support; the question goes to the reply as an `[ASK AUTHOR: ...]` line. An external fact the user supplied from memory (a faculty member's recent paper, a deadline, a character limit) is used only as supplied and comes back in the reply as a `[VERIFY: ...]` line.
2. **Identify the document type and its rules.** Résumé or CV, letter or statement, field or form, email or message. Note region, field, seniority and any instruction from the target. For conventions see [résumés and CVs](references/resumes-and-cvs.md), [letters and statements](references/letters-and-statements.md), [profiles and outreach](references/profiles-and-outreach.md).
3. **Build the evidence inventory.** Per role or episode: what the organization does, what the candidate was asked to do, what they personally did, what changed, with which numbers and who can confirm them. Ask for missing scale, before and after, and frequency. Estimates are allowed only when the candidate confirms them, are marked in notes, and err low.
4. **Read the target and map it.** Rank the stated requirements. Label each as direct evidence, adjacent evidence, transferable evidence, or gap. Gaps are never filled with fiction. Decide apply, stretch, or skip together with the candidate when the match is weak.
5. **Apply the mode recipe.**
   - *Build:* choose the section order for the career stage, write accomplishment bullets, keep one master and archive old versions.
   - *Tailor:* copy from the master, rewrite the summary for the role, lead each role with its two most relevant true bullets, reorder skills, use the posting's own terms only where they describe real work, trim to the length band, log the version.
   - *Letter:* write a one-sentence thesis of fit, then an opening with a specific hook, two or three evidence paragraphs mapped to the target's needs, and a short close. For statements, answer every prompt question and tie fit to program details the user supplies.
   - *Profile:* keep titles, dates and numbers identical to the résumé; expand wording, not history. For short answers, answer the exact question and stop.
   - *Outreach:* one reader, one specific reason, one easy ask. Facts about the recipient come from public sources the user can name.
6. **Draft clean.** The document holds only text a recruiter or committee could read as written: no markers, no bracket placeholders, no notes. Settle every gap as in [Gaps in reader-facing documents](#gaps-in-reader-facing-documents). Never smooth a gap with a plausible guess.
7. **Self-check.** Run [eval.md](eval.md) on the draft and fix every failure. If `anti-slop-editing` is available, run it as a final pass with career clichés in scope; otherwise apply the cliché checks in eval.md. If the user has a voice profile, apply it with `author-voice` before the final check. For high-stakes documents (a fellowship statement, an executive résumé), suggest `independent-review` for a fresh reader.
8. **Return** the document, then the reply note (see Output): what changed and why, assumptions, open questions as marker lines, and what the user must verify with the target.

## Rules

- **Truth first.** Employers, titles, dates, degrees, credentials, publications, tools, languages and numbers come from the candidate. Every line may be questioned in an interview or a background check. No exception for "everyone does it".
- **Tailoring is selection and wording.** Reorder, emphasize, drop and rephrase true material. Never change a title or date, add a tool the candidate has not used, or merge results from different employers into one sentence. Exception: a title may be paired with a plain functional description when the official title misleads, and the candidate agrees.
- **Numbers belong to the candidate.** Use exact figures when supplied. A range, a floor ("40+") or a rounded estimate needs the candidate's confirmation. Skip percentages with no baseline, figures the candidate cannot explain, and anything confidential. Reason: a number that cannot be defended costs more credibility than no number. A request to "add numbers", "quantify" or "make it more impressive" is not a source of numbers: when none were supplied, keep the true wording, put no figure and no `[X]` slot in the document, and ask for the figures in the reply (`[ASK AUTHOR: ...]` lines). Exception: when no honest number exists, state scope or outcome in plain true words.
- **Mirror the posting's terms only where they are true.** Use the exact term when it names work the candidate did; otherwise keep the candidate's own term. Keyword lists, hidden text and synonym piles are defects. A required or preferred skill absent from the candidate's material (a tool, language, credential) is a gap: it stays out of Skills, summary and bullets, even as "familiar with", unless the candidate confirms real use. Reason: the human reader and the interview both test the claim.
- **Length and format norms are common practice, not law.** Page counts, word counts, file types, section order and character limits vary by region, field, institution and portal. State which norm is used and tell the user to verify. The target's written instruction wins.
- **Flag regional conventions.** Photo, date of birth, marital status, nationality, referees, and "CV" versus "résumé" naming differ by country. When the market is unknown, omit sensitive personal fields and ask. Do not apply one country's norms to another.
- **Fit is specific or it is not fit.** Reasons for a role or program must name something real about it that the user supplied or that is publicly checkable. If the organization name could be swapped for another and the sentence still works, rewrite it or cut it. Never invent a faculty relationship, mutual contact, prior conversation, referral, or a paper, talk or project of the recipient. No "as we discussed" unless the user confirms a real exchange. When the user gave nothing specific about the recipient, write a plainer message with no claim of familiarity and ask for the hook in the reply.
- **One story, in the reader's terms.** A letter, statement or profile follows one line: who the candidate is, the work that matters to this reader and what came of it, and why this role or programme. Each paragraph moves that line on. Describe projects by the problem and the result a reader outside the team understands, not by internal names, codes, timestamps or tool lists. A résumé line says what the candidate did and what changed because of it. When the user supplies an example letter, a template or a format the target requires, match its length, structure and register.
- **Gaps are stated once, plainly.** A skill gap, career change, employment gap or stretch role gets one short sentence with the closest true evidence, not an apology and not a cover-up. Dates stay accurate.
- **The document reads as finished.** Unless the user asked for a draft to edit, a document a recruiter, committee or contact will read holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` markers, no bracket placeholders (`[Company]`, `[N] years`, `[X]%`), and no notes to the author: no "as requested", no "tailored for", no per-paragraph source notes, no process narration. Reason: a placeholder in a file that goes out looks unfinished, and a note to the author gets sent with it. Gaps become a plain fact or an omission; questions go to the reply and, when a file is written, to `open-questions.md`. Never reword a gap into a confident claim to avoid asking. Exception: the user asked for a draft to edit; then markers stay at the point of the gap and the reply says it is a draft. A marker may also stay in an author-facing artifact: the tailoring and fit analysis, requirement-to-evidence map, gap list, evidence inventory and the reply note itself are for the candidate, not the reader.
- **Personal and hardship material is proportionate.** Include it only when the prompt invites it or it is needed context, and tie it to readiness. Exception: none for fabricated or embellished events.
- **Drafts, not sends.** Never send, submit or contact anyone. The user reviews every external message. Outreach stops the moment the recipient declines.
- **Other languages.** The English cliché and phrase lists in this skill do not transfer. For Vietnamese or other languages, apply the structural, evidence and preservation checks, and say that the lexical lists were skipped. Document conventions (photo, personal data, length) also differ by country; ask or have the user verify.
- **Cliché control.** Phrases such as "results-driven", "passionate", "team player", "proven track record", "responsible for" and "excited to leverage" are signals to replace with evidence. Exception: keep a phrase the posting requires as a term of art, or one the candidate genuinely says.
- **Reports are short and true.** List what changed and why. Do not claim improvements in match, readability or interview odds that were not measured.
- **Write like the person, not the process.** A letter, statement, email or form answer reads as one person writing to one reader: no headings, bullets or labels (except a criteria letter the employer structures, and the section headings and bullets a résumé or CV uses by norm); plain transitions with no signposting ("In summary", "I am writing to"); prose when there are fewer than about four parallel items. Say each gap, limit or "I have not yet" once, at the claim it limits; do not restate the pitch in the close or add a second thank-you or offer. Keep the candidate's own person, contractions and formality, and the recipient's level of formality. Reason: committees and recruiters read hundreds of these, and process-shaped structure and repeated hedging read as written by a template. Exception: a genre norm that requires structure; faithfulness rules are unchanged (every qualifier, number and gap still appears once).

## Gaps in reader-facing documents

A gap is something the candidate's material does not say. The document states it in reader language or leaves the sentence out; the question goes to the author.

| Gap | In the document | In the reply and `open-questions.md` |
| --- | --- | --- |
| no figure for a bullet | the true wording with no number ("Handled the billing-escalation queue for a support team") | `[ASK AUTHOR: tickets per week, team size, response-time change?]` |
| no date or end date | the dates the material gives; never a guessed month; "2022 to 2024" stays as supplied | `[ASK AUTHOR: start and end month for the Brookline Data role?]` |
| required skill the candidate lacks | nothing in Skills, summary or bullets; the nearest true work, stated as it is | listed under Gaps in the note; `[ASK AUTHOR: any real use of Terraform, even on a side project?]` |
| no hook about the recipient or program | a plainer message or paragraph with no claim of familiarity | `[ASK AUTHOR: one paper or project of theirs you have read, and what you took from it]` |
| no named recipient | "Dear Hiring Manager", "Dear Admissions Committee" | `[ASK AUTHOR: name of the hiring manager, if known?]` |
| external fact from memory (deadline, faculty detail, limit) | used only if the user stated it; otherwise omitted | `[VERIFY: deadline and word limit against the current program page]` |
| prompt part with no material | the sentence is omitted or kept to what the material supports; a short statement of the plain situation if the reader expects an answer ("I have not yet done research outside my thesis.") | `[ASK AUTHOR: ...]` for what would answer it |

`open-questions.md` sits beside the deliverable when a file is written and there are questions. Number the items and use the same numbering in the reply:

```markdown
# Open questions: cover letter, Northfield Labs

1. [ASK AUTHOR: how many tickets a week did the billing queue take?]
   Blocks: paragraph 2. The letter says: "I handled the billing-escalation queue."
2. [VERIFY: the application deadline, from the posting page]
   Blocks: nothing in the letter; the date is not stated in it.
```

When the user restricts the output to one file ("save only the resume"), skip `open-questions.md` and put the questions in the reply. Hosted tools or chat without files: reply only.

## Output

Return the document first, in the form the target expects (plain text or Markdown the user can paste into a word processor; no layout tricks that break parsing); the file holds the document and nothing else. Then a note in the reply of at most 15 lines. The note is for the candidate, not the reader, and may carry markers:

- **Changes:** what was reordered, rewritten, added or cut, and why (before and after for any edited bullet when asked).
- **Assumptions:** anything inferred and not confirmed.
- **Open items:** the `[ASK AUTHOR: ...]` and `[VERIFY: ...]` lines, one per line, numbered like `open-questions.md`.
- **Verify with the target:** length, format, file type, required sections, deadline, and any regional convention applied.
- **Gaps:** requirements with no or weak evidence, ranked, and how the document handles them.

For tailoring also give a two-to-three sentence throughline: why this candidate fits this role, using only supported claims.

## Reference files

| File | Load when |
| --- | --- |
| [résumés and CVs](references/resumes-and-cvs.md) | building, tailoring, shortening or checking a résumé or academic CV; bullets, numbers, sections, parsing, career change |
| [letters and statements](references/letters-and-statements.md) | writing a cover letter, statement of purpose, personal statement, motivation letter or award essay |
| [profiles and outreach](references/profiles-and-outreach.md) | LinkedIn, portfolio case studies, story banks, form answers, cold or networking email, reference or offer messages, regional email conventions |
| [evidence inventory template](assets/evidence-inventory-template.md) | the user has little written material, or numbers and scope are missing |
| [eval.md](eval.md) | before returning any document |

## Examples

Bullet, duty to evidence (the numbers are the candidate's, confirmed):

- Before: "Responsible for customer support tickets."
- After: "Resolved about 40 tickets a week for a 6-person support team; kept average first reply under 2 hours."
- Note: if the candidate cannot confirm the figures, write what is true, such as "Handled the billing-escalation queue for a 6-person support team", and ask for scale.
- Request "make it more impressive with numbers" and no figures supplied: the résumé keeps "Handled the billing-escalation queue for a support team" with no figure; the reply asks `[ASK AUTHOR: tickets per week, team size, response-time change?]`. Do not insert a typical figure, and do not leave a `[X]` slot in the résumé.

Cover letter opening, generic to specific (invented facts, replace with the user's):

- Before: "I am writing to express my strong interest in the Data Analyst position at your innovative company."
- After: "Your posting asks for someone who can move reporting from spreadsheets to a shared warehouse. I did that migration for a 12-person finance team last year, and I would like to do the same for yours."
- Note: the second version needs the user to supply the migration and the team size; the posting supplies the need.

Outreach, vague ask to easy ask:

- Before: "I would love to pick your brain about breaking into UX."
- After: "I read your write-up on onboarding research. I am moving from teaching into UX research and have one study to show. Could I send you two questions by email instead of asking for a call?"

Outreach to a prospective supervisor, only supplied facts:

- Before: "I have long admired your groundbreaking work and would love to work with you."
- After: "I am applying to the MSc in Ecology this autumn. I read your 2025 paper on hedgerow connectivity and ran a smaller survey on the same question for my thesis. Are you taking students for next year?"
- Note: the paper and the thesis come from the user. With no paper supplied, the message says only what is true ("I am applying to the MSc in Ecology this autumn and am writing to ask whether you take students for next year") and the reply asks `[ASK AUTHOR: one paper of theirs you have read, and what you took from it]`.
