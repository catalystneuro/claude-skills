# Stacked PR Workflow

Used when the user chose the stacked PRs delivery mode. The conversion still runs end-to-end;
the work is committed on a chain of branches so it can be opened as one pull request per data
stream at the end of Phase 7. Requires git 2.38 or later (`--update-refs`) and `gh`
authenticated with push access to the conversion repo.

## Branches

One `setup` branch, then one branch per data stream, each created from the previous one:

```
main ← setup ← <reference_stream> ← <stream_2> ← ... ← <stream_n>
```

- Name stream branches after the stream, short and with underscores (e.g. `medpc_behavior`,
  `fiber_photometry`, `optogenetics`).
- Put the stream that serves as the timing reference in Phase 4 first, so later streams can
  align to it.
- Record the branch order in `conversion_notes.md` under `## Delivery Mode`.

## What goes on each branch

**`setup`**: everything from Phases 1 to 4 (`conversion_notes.md`, collected metadata), plus
the repo scaffold from Phase 5: `pyproject.toml`, `README.md`, `make_env.yml`, session-level
`metadata.yaml` (NWBFile, Subject), the NWBConverter with no data interfaces yet,
`convert_session.py` and `convert_all_sessions.py`.

**Each stream branch**: that stream's interface code (or NeuroConv interface usage), its entry
in the converter, its metadata, its alignment logic, its tests and fixes, and its review
notebook from Phase 7. The combined demo notebook goes on the last branch.

## Creating the branches

After the initial `.gitignore` commit on `main` (Phase 1, Step 0b) is pushed:

```bash
git checkout -b setup
```

In Phase 5, once the setup work is committed, start each stream from the previous branch:

```bash
git checkout -b <stream>   # from the previous branch in the stack
# write and commit the stream's code
```

Whenever a phase says to push, push the current branch instead of `main`:

```bash
git push -u origin HEAD
```

## Changing a lower branch

Testing (Phase 6) and notebooks (Phase 7) often touch a branch below the top of the stack.
Commit on the branch the change belongs to, then carry it up to every branch above it:

```bash
git checkout <stream>          # the branch the change belongs to
git add <files> && git commit -m "<message>"
git checkout <top_branch>      # the last branch in the stack
git rebase --update-refs <stream>
git push --force-with-lease origin <every branch above <stream>>
```

`--update-refs` moves the intermediate branches along with the top one.

## Opening the PRs

At the end of Phase 7, push every branch and open the PRs from the bottom of the stack up,
each based on the branch below it:

```bash
git push -u origin setup <reference_stream> <stream_2> ... <stream_n>
gh pr create --base main --head setup --title "Set up <lab> conversion" --body "<body>"
gh pr create --base setup --head <reference_stream> --title "Add <stream>" --body "<body>"
gh pr create --base <reference_stream> --head <stream_2> --title "Add <stream_2>" --body "<body>"
```

Each stream PR body states:
- what the stream is and which source files it reads
- which NeuroConv interfaces it uses, or for a custom interface, the reason recorded in
  `conversion_notes.md`
- the NWB types and extensions it writes
- the path of its review notebook

## Reviewing and merging

Reviewers merge from the bottom of the stack. When a PR merges and its branch is deleted,
GitHub retargets the next PR to `main`. A reviewer who fixes a stream commits on that
stream's branch and carries the fix up as in "Changing a lower branch".
