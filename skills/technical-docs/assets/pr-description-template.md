# type(scope): what changed
<!-- The title is the first line of the file. About 70 characters or fewer including the type prefix; not the branch name. Delete this comment. -->

## Summary

<Two to four sentences: the problem and what this change does about it, at product level.>

```text
<Smallest view of the change's shape: file tree, call tree, pseudocode or shaped diff.
Keep only the calls, files and boundaries the reviewer needs. Delete if the sentence is enough.>
```

## Changes

- <Area>: <what changed>
- <Area>: <what changed>
- Tests: <added or changed>
- Docs: <updated pages, or "none needed">

## Evidence

Before:

<Screenshot, failing test, or old console output.>

After:

<Screenshot, same test now passing, or new console output.>

Reproduce:

```bash
<command a reviewer can rerun>
```

```text
<expected output>
```

Test status: <actual result of the run, or "Not run">. Manual testing: <what was done and seen, or "none">.

## Risk and rollout

- Door: <two-way | one-way>. <Why. One-way examples: destructive migration, public API removal, new on-disk format, sent messages.>
- Blast radius: <what breaks if this is wrong: consumers, data, screens>
- Rollout: <plain merge | flag name | staged deploy>
- Rollback: <how to undo, or "cannot be undone: ...">
- Watch after merge: <signal and threshold, or "nothing specific">

## Reviewer focus

- <File or decision to read slowly, and why>
- <Second place>
- Out of scope: <related things deliberately not changed>

## Breaking changes

<Delete this section if there are none. Otherwise: what breaks, who is affected, migration path, before/after usage, deprecation timeline.>

## Related

- Closes #<n>
- Spec or ticket: <link, or "no spec available">

<details>
<summary>Design notes and alternatives considered</summary>

<Trade-offs, rejected options, benchmark detail. Delete if empty.>

</details>
