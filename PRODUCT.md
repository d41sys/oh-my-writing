# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vanilla JavaScript with Vite in `site/`. `npm run build` there writes static files to `site/dist/`.

## Users

People who write with an AI coding agent (Claude Code, Codex, omp) and want drafts and edits without stock AI phrasing or invented facts. Second audience, confirmed: developers comparing skill packs, who look for evidence.

## Product Purpose

Oh My Writing is a set of eleven Agent Skills. An agent loads the matching skill when asked to draft, edit, check or review text. Success for a visitor to the site: they see what a skill does to a real piece of text and copy the install command.

## Positioning

The skills instruct the agent to preserve source facts and flag gaps with markers such as `[ASK AUTHOR: …]` or `[VERIFY: …]`. Saved runs show what happened in specific cases; they do not guarantee the same result on another draft.

## Operating Context

Install with `npx github:d41sys/oh-my-writing`, then ask the agent in plain words. While the repository is private, Git must have read access.

## Capabilities and Constraints

- Eleven skills, listed in `README.md`.
- Hosts: Claude Code, Codex, omp.
- Undecided: the public URL of the site.

## Brand Commitments

Name: Oh My Writing. No logo, no fixed colours or typefaces.

## Evidence on Hand

- Benchmark cases in `evals/cases/` (the inputs are made-up test fixtures) and saved model outputs in `evals/results/*/runs/` (real runs). The site shows these as before and after.
- Benchmark tables in `README.md` and `docs/BENCHMARK.md`. The user chose not to show benchmark numbers on the site.
- Absent, never to be invented: user quotes, customer names or logos, usage counts.

## Product Principles

1. Show the text, not a description of it.
2. Nothing on the page that the repository cannot back with a file.
3. A gap is shown as a gap.
