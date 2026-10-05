# Section Recipes

Before each section, answer its pre-writing questions in notes; write prose only after. Recipes describe what each paragraph does, not sentences to copy: borrowed sentence skeletons make every paper sound the same.

## Title
Specific claim or object, not a field. A reader should guess the finding. Short; no colon-title by reflex.

## Abstract
Write a draft first to force focus; rewrite it last, when the results and story are frozen.

Pre-writing: what problem; why no established solution; what we contribute; why it works; what new insight.

Pick one structure:
- **Challenge → contribution**: task → challenge (limitation + reason) → contribution named in 1–2 sentences (name it, don't list its steps) → benefit → evidence.
- **Challenge → insight → contribution**: as above, with one insight sentence before the contribution. Best for insight/analysis papers.
- **Multiple contributions**: task → one contrast with prior work if needed → each contribution with its advantage in one sentence → evidence.

Rules: first sentence specific to this paper (no "LLMs have achieved remarkable..." opener); at least one concrete number; self-contained; no citations; no undefined acronyms (spell out AUROC etc.); 150–250 words; one message per sentence, short sentences (aim for about 20–25 words on average; split any sentence that carries two results). Introduce the task before the setup details, one step per sentence. The last sentence states what the reader should remember, not a generic "these results demonstrate" summary; it may only restate results already given, with their conditions (dataset, split, setting) attached. Never aggregate, extrapolate, or infer a threshold in the closing sentence (no "at least X on all", no "requires closer to Y"). A reviewer must be able to write "X is good for Y in the context of Z" after reading it.

## Introduction
About one page, at most 1.5; a clear, important contribution visible by page 2.

Backward plan: (1) technical problem and why unsolved; (2) contribution type; (3) why it works / new insight; (4) which prior work leads the reader to our challenge.

Forward order: task/application → challenge for prior methods → our approach → evidence preview → contributions.

Five-question check (one paragraph each is a valid intro): What is the problem? Why is it important? Why is it hard (why do obvious approaches fail)? Why is it unsolved (what is wrong with prior solutions, how do we differ)? What are the key components of our approach and results, including specific limits?

Introduce the problem with a concrete example, not with a list of citations saying the problem matters.

**Opening options**
1. Niche task: define it by its input and output, then 2–3 applications.
2. Familiar task: go straight to why it matters now.
3. New setting: the general task and its value, then narrow to this paper's setting with exact input/output.
4. Strong case: in paragraph 1, state importance, how prior methods work, and where and why they fail.

**Challenge options** (discuss prior work only around the challenge we solve)
1. Existing task: general challenge → traditional methods and their limit → recent methods and their limit with its technical reason; the last limit is our problem.
2. Insight rooted in classic work: mainstream limit → a classic line that had a similar insight → why it was insufficient → why modern methods still fail → us.
3. Novel task: state the goal, then split the difficulty into N independent reasons, each with its observable symptom and technical cause.

**Approach options**
1. One contribution with several advantages: name the contribution, point to Figure 1, state the key innovation, how it works concretely, and each advantage over prior methods.
2. Two contributions: contribution 1 and its advantage → the challenge it leaves → contribution 2 as the answer.
3. New module on an existing pipeline: the pipeline we build on → the observation that motivates the module → the module → why it beats the generic alternative.
4. Observation-driven (fits analysis papers): the key finding first → the observation behind it → what we did with it → what it leads to.

**Contributions**: 2–4 falsifiable bullets, 1–2 lines each, each with a forward reference to the section, table, or figure holding its evidence. A reviewer must be able to agree or disagree with each. Bad: "We conduct extensive experiments", "we improve the visualization". Preview the headline result before the bullets.

**No roadmap paragraph** ("The rest of this paper is organized as..."). The forward references in the bullets and the narrative already map the paper.

Respect predecessors before stating their limits. Consider a page-one figure carrying the core idea or the key result.

## Related work
**Position: decide per paper.**
- Early (Section 2) when readers need prior methods to understand the challenge, when the venue expects it (most ML/CV/NLP venues), or when close competitors must be separated before our method appears.
- Late (after results) when the problem is new or the reader needs our idea first to understand the comparison; keep the 2–3 closest papers in the intro either way.

Content:
- 2–4 topics by mechanism, assumption, or research question; never chronological paper-by-paper summaries.
- Paragraph: scope → shared paradigm of the line → its limit tied to our challenge → how we differ, in technical terms.
- Compare and contrast: if a method applies to our setting, it appears as a baseline; if not, say why.
- Write a neutral survey first, then rewrite it from our angle. Check "first"/"pioneer" claims against those papers' own related work.
- Credit is not like money: generous credit to prior work does not reduce ours. Never imply an old idea is ours. Never hide the strongest competitor.
- At least about one page for ML venues.

## Method
Pre-writing: list modules; for each, answer how it runs, why it is needed, why it works. Draw the pipeline figure sketch first and derive subsections from it.

- **Overview**: setting → core contribution → pointer to the pipeline figure → what each subsection covers.
- **Each module has three parts**: motivation (the problem that makes the module necessary) → design (structures first, then the forward process from input to output, in execution order) → advantage over the obvious alternative, tied to a measurable behavior. Draft the design first, then add motivation and advantage.
- Introduce with an example, then the general case.
- Notation defined at first use; assumptions before results; intuition next to each equation; say why an equation matters before showing it.
- Every parameter: show how to set it, or that its exact value barely matters.
- Justify complexity: the paper implicitly claims this is the simplest way to get results this good, so show that simpler alternatives fail. If the method is simple, present simplicity as an advantage.
- Implementation details at the end or in the appendix.
- Clarity check: logic (summarize the section's logic; is it smooth?), paragraph (first sentence says what the paragraph does), sentence (why is this sentence needed? does it follow from the previous one? are terms stable?).

For analysis/benchmark papers, "method" = protocol: define the estimand, the measurement, the parser/extraction rule, and every operational predicate exactly as the code implements it.

## Experiments
Three questions: (1) better than strong, recent baselines under a fair, identical protocol? (2) which component or factor causes the effect? (3) does it hold in harder or shifted settings, and where does it fail?

Plan: claim → validation experiment; module/key parameter → ablation. Order: setup → main result → supporting experiments → ablations/analysis, ordered as an argument. Put each control next to the claim it tests.

Each result paragraph: topic sentence = the claim tested → evidence with numbers → what the reader should notice → link to the next question. Refer to "Table N" in the sentence that interprets it, on the same page.

Evidence quality:
- An experiment is good when its outcome would differ depending on which hypothesis is true; one decisive experiment beats many weak ones.
- Baselines are the strongest plausible alternatives, tuned with the same effort as our method; "it works" is weaker than "it beats what people would otherwise use". Include the simplest baseline that could work.
- Several qualitatively different lines of evidence pointing the same way beat many similar experiments.
- Real data over synthetic; if data is modified or synthetic, say how and why.
- Qualitative examples: say how they were chosen; show randomly selected examples next to the best ones.
- Report variance, sample size, and number of runs; a single run per cell is a stated limitation.
- State all parameters and settings; point to code and data.

## Limitations, discussion, conclusion
- Conclusion: problem + key idea → strongest evidence → what it changes. Rephrase; never copy the abstract or intro.
- Limitations: 2–4 real scope boundaries (data regime, assumption, setting, single-sample design). Distinguish scope limits from technical defects, which must be stated plainly. All generic caveats live here and nowhere else.
- No new claims, no self-negation in the final paragraph; future work concrete or absent.

## Appendix
Full protocol, prompts, extraction rules, parameter tables, extra results, examples a reviewer would ask to inspect. Nothing needed to understand the contribution lives only here.
