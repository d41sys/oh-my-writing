# Contributing

Contributions of all kinds are welcome: bug reports, a failing writing example, a new benchmark case, a rule fix, or a new skill.

## Report a problem

Open an issue with:
1. what you asked, word for word;
2. the material you gave, or a trimmed version;
3. what came back, and what was wrong (an invented fact, a lost hedge, AI-sounding wording, the wrong skill loaded);
4. the host and model (Claude Code, Codex or omp, plus the model name).

A real failing example is the most useful contribution. It can become a benchmark case.

## Set up

```bash
git clone https://github.com/d41sys/oh-my-writing.git && cd oh-my-writing
node bin/oh-my-writing.mjs install --dry-run        # see what the installer would do
for d in skills/*/; do uvx --from 'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref' skills-ref validate "$d"; done
for t in tests/*/; do uv run --with pytest --with pyyaml --with numpy --with matplotlib python -m pytest "$t" -q -p no:cacheprovider; done
python3 evals/grade.py --validate
```

You need Python 3.10+, [uv](https://docs.astral.sh/uv/) and Node 18+.

## Change a skill

Each skill is `skills/<name>/`, laid out like this:

| Path | Purpose |
|---|---|
| `SKILL.md` | Frontmatter plus a workflow under 500 lines |
| `references/` | Detail loaded on demand |
| `assets/` | Templates |
| `scripts/` | Python standard library only, with tests in `tests/<name>/` |
| `eval.md` | The self-check run before returning |
| `agents/openai.yaml` | Codex metadata |

Rules that `tests/_meta` enforces or reviewers will ask about:

1. **Bump `metadata.version`** in `SKILL.md` on every change.
2. **Write in your own words.** Do not paste text from other skill packs or articles. Name sources only in README Acknowledgments and `THIRD_PARTY_NOTICES.md`. Before sending a PR, run `python3 evals/source_similarity.py --out /tmp/sim.md`. Any new long verbatim run with a source must be reworded.
3. **Write general rules, not fixes for one test.** A rule must make sense to a writer who has never seen the benchmark. Skill text and descriptions must not contain names, phrases or answers from `evals/cases/`. `_meta` checks for 7-word runs from cases and fixtures, and for 5-word runs from case prompts in descriptions.
4. **Never let a skill invent facts.** Gaps use only `[ASK AUTHOR: …]`, `[VERIFY: …]` or `[UNTESTED]`, outside the reader-facing text.
5. **Keep descriptions as task classes** ("PR descriptions from a diff"), not copies of one prompt.

## Add a benchmark case

Cases are JSON files in `evals/cases/<skill>/`. Copy a nearby case and keep its format. `python3 evals/grade.py --validate` checks it.

1. **Write the prompt as a real user would.** Use realistic material. Put real document folders in `evals/fixtures/`.
2. **Write checks for what the task means**: facts kept, nothing invented, gaps marked. Avoid checks that require one particular heading or phrase.
3. **Try the checks on real outputs from every condition** before relying on them. When you later loosen a check, the note must quote the correct output it rejected.
4. **To measure generalization, add held-out cases** (`heldout-*`) and never tune skills against them.

## Pull requests

- One topic per PR. Explain the problem, the change and the evidence: test output, or a before/after benchmark on the affected cases.
- All tests, validation and `--validate` must pass.
- No personal data in cases or fixtures. Use invented names and organisations.
- By contributing, you agree that your contribution is licensed under the repository's license (MIT; CC-BY-SA 4.0 for `skills/technical-docs/`).
