---
name: career-documents
description: "Writes and edits truthful career documents from the candidate's real material: résumés, academic CVs, tailoring to a job posting, cover letters, statements of purpose, personal statements, motivation letters, LinkedIn and portfolio profiles, short application-form answers, and cold, networking, warm-intro, thank-you or prospective-supervisor emails. Never invents experience, dates, titles, skills, contacts or numbers. Use when the user asks to write, rewrite, tailor, shorten or review a resume, CV, cover letter, SOP, personal statement, motivation letter, LinkedIn headline or About section, application answer, or a job-search, networking or academic outreach email."
license: MIT
metadata:
  version: "1.1"
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

For a thin source, use [evidence inventory template](assets/evidence-inventory-template.md) to run a short interview first. If the user will paste text into a hosted tool, suggest leaving out ID numbers, home address, birth date and similar personal data, and use placeholders.

## Workflow

Modes: **build** (new or refreshed master), **tailor** (one target), **letter** (cover letter, statement, award essay), **profile** (LinkedIn, portfolio, short answers), **outreach** (cold, networking, academic, warm intros, thank-yous, references, offers). Steps 1 to 4 apply to every mode.

1. **Fix the truth boundary.** List what the candidate supplied. Anything not on that list is unknown, not available for use. Missing detail becomes an `[ASK AUTHOR: ...]` marker, a question, or is left out. An external fact the user supplied from memory (a faculty member's recent paper, a deadline, a character limit) becomes `[VERIFY: ...]`.
2. **Identify the document type and its rules.** Résumé or CV, letter or statement, field or form, email or message. Note region, field, seniority and any instruction from the target. For conventions see [résumés and CVs](references/resumes-and-cvs.md), [letters and statements](references/letters-and-statements.md), [profiles and outreach](references/profiles-and-outreach.md).
3. **Build the evidence inventory.** Per role or episode: what the organization does, what the candidate was asked to do, what they personally did, what changed, with which numbers and who can confirm them. Ask for missing scale, before and after, and frequency. Estimates are allowed only when the candidate confirms them, are marked in notes, and err low.
4. **Read the target and map it.** Rank the stated requirements. Label each as direct evidence, adjacent evidence, transferable evidence, or gap. Gaps are never filled with fiction. Decide apply, stretch, or skip together with the candidate when the match is weak.
5. **Apply the mode recipe.**
   - *Build:* choose the section order for the career stage, write accomplishment bullets, keep one master and archive old versions.
   - *Tailor:* copy from the master, rewrite the summary for the role, lead each role with its two most relevant true bullets, reorder skills, use the posting's own terms only where they describe real work, trim to the length band, log the version.
   - *Letter:* write a one-sentence thesis of fit, then an opening with a specific hook, two or three evidence paragraphs mapped to the target's needs, and a short close. For statements, answer every prompt question and tie fit to program details the user supplies.
   - *Profile:* keep titles, dates and numbers identical to the résumé; expand wording, not history. For short answers, answer the exact question and stop.
   - *Outreach:* one reader, one specific reason, one easy ask. Facts about the recipient come from public sources the user can name.
6. **Draft with markers.** Keep unresolved items visible in the text. Never smooth a gap with a plausible guess.
7. **Self-check.** Run [eval.md](eval.md) on the draft and fix every failure. If `anti-slop-editing` is available, run it as a final pass with career clichés in scope; otherwise apply the cliché checks in eval.md. If the user has a voice profile, apply it with `author-voice` before the final check. For high-stakes documents (a fellowship statement, an executive résumé), suggest `independent-review` for a fresh reader.
8. **Return** the document plus a short note: what changed and why, assumptions, open questions, and what the user must verify with the target.

## Rules

- **Truth first.** Employers, titles, dates, degrees, credentials, publications, tools, languages and numbers come from the candidate. Every line may be questioned in an interview or a background check. No exception for "everyone does it".
- **Tailoring is selection and wording.** Reorder, emphasize, drop and rephrase true material. Never change a title or date, add a tool the candidate has not used, or merge results from different employers into one sentence. Exception: a title may be paired with a plain functional description when the official title misleads, and the candidate agrees.
- **Numbers belong to the candidate.** Use exact figures when supplied. A range, a floor ("40+") or a rounded estimate needs the candidate's confirmation. Skip percentages with no baseline, figures the candidate cannot explain, and anything confidential. Reason: a number that cannot be defended costs more credibility than no number. A request to "add numbers", "quantify" or "make it more impressive" is not a source of numbers: when none were supplied, keep the true wording, put `[ASK AUTHOR: ...]` where the figure belongs, and list the questions. Exception: when no honest number exists, state scope or outcome in plain true words.
- **Mirror the posting's terms only where they are true.** Use the exact term when it names work the candidate did; otherwise keep the candidate's own term. Keyword lists, hidden text and synonym piles are defects. A required or preferred skill absent from the candidate's material (a tool, language, credential) is a gap: it stays out of Skills, summary and bullets, even as "familiar with", unless the candidate confirms real use. Reason: the human reader and the interview both test the claim.
- **Length and format norms are common practice, not law.** Page counts, word counts, file types, section order and character limits vary by region, field, institution and portal. State which norm is used and tell the user to verify. The target's written instruction wins.
- **Flag regional conventions.** Photo, date of birth, marital status, nationality, referees, and "CV" versus "résumé" naming differ by country. When the market is unknown, omit sensitive personal fields and ask. Do not apply one country's norms to another.
- **Fit is specific or it is not fit.** Reasons for a role or program must name something real about it that the user supplied or that is publicly checkable. If the organization name could be swapped for another and the sentence still works, rewrite it or cut it. Never invent a faculty relationship, mutual contact, prior conversation, referral, or a paper, talk or project of the recipient. No "as we discussed" unless the user confirms a real exchange. When the user gave nothing specific about the recipient, write a plainer message or place an `[ASK AUTHOR: ...]` marker for the hook.
- **Gaps are stated once, plainly.** A skill gap, career change, employment gap or stretch role gets one short sentence with the closest true evidence, not an apology and not a cover-up. Dates stay accurate.
- **Markers.** Use only three kinds: `[ASK AUTHOR: ...]` when the candidate knows or decides it (a number, scope, experience, intent, which of two options), `[VERIFY: ...]` when a source exists or must be found and checked (an external fact, source or rule to check with the target), and `[UNTESTED]` for a code sample or command that was not run. Do not invent other kinds. Markers stay in the draft until resolved; never reword a gap into a confident claim to avoid one.
- **Personal and hardship material is proportionate.** Include it only when the prompt invites it or it is needed context, and tie it to readiness. Exception: none for fabricated or embellished events.
- **Drafts, not sends.** Never send, submit or contact anyone. The user reviews every external message. Outreach stops the moment the recipient declines.
- **Other languages.** The English cliché and phrase lists in this skill do not transfer. For Vietnamese or other languages, apply the structural, evidence and preservation checks, and say that the lexical lists were skipped. Document conventions (photo, personal data, length) also differ by country; ask or have the user verify.
- **Cliché control.** Phrases such as "results-driven", "passionate", "team player", "proven track record", "responsible for" and "excited to leverage" are signals to replace with evidence. Exception: keep a phrase the posting requires as a term of art, or one the candidate genuinely says.
- **Reports are short and true.** List what changed and why. Do not claim improvements in match, readability or interview odds that were not measured.

## Output

Return the document first, in the form the target expects (plain text or Markdown the user can paste into a word processor; no layout tricks that break parsing). Then a note of at most 15 lines:

- **Changes:** what was reordered, rewritten, added or cut, and why (before and after for any edited bullet when asked).
- **Assumptions:** anything inferred and not confirmed.
- **Open items:** the `[ASK AUTHOR: ...]` and `[VERIFY: ...]` markers, one line each.
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
- Request "make it more impressive with numbers" and no figures supplied: keep "Handled the billing-escalation queue for a support team", add `[ASK AUTHOR: tickets per week, team size, response-time change?]`, and list those questions in the note. Do not insert a typical figure.

Cover letter opening, generic to specific (invented placeholders, replace with the user's facts):

- Before: "I am writing to express my strong interest in the Data Analyst position at your innovative company."
- After: "Your posting asks for someone who can move reporting from spreadsheets to a shared warehouse. I did that migration for a 12-person finance team last year, and I would like to do the same for yours."
- Note: the second version needs the user to supply the migration and the team size; the posting supplies the need.

Outreach, vague ask to easy ask:

- Before: "I would love to pick your brain about breaking into UX."
- After: "I read your write-up on onboarding research at [company]. I am moving from teaching into UX research and have one study to show. Could I send you two questions by email instead of asking for a call?"

Outreach to a prospective supervisor, only supplied facts:

- Before: "I have long admired your groundbreaking work and would love to work with you."
- After: "I am applying to the MSc in Ecology this autumn. I read your 2025 paper on hedgerow connectivity and ran a smaller survey on the same question for my thesis. Are you taking students for next year?"
- Note: the paper and the thesis come from the user. With no paper supplied, use `[ASK AUTHOR: one paper of theirs you have read, and what you took from it]` instead of naming one.
