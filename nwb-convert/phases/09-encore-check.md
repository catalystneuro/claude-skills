## Phase 9: Encore Check

**Goal**: Check the converted NWB files against the paper they come from, before upload. [Encore](https://encorescience.org)
has AI agents read the paper, write down its key findings and how to test each one, and then test them on the data.
Along the way they report problems with the data that NWB Inspector does not catch: units or clocks that are wrong,
metadata that disagrees with the files, and data the paper describes but the files do not hold. Fixing these before
upload is much cheaper than fixing a published Dandiset.

**Entry**: Every session is converted in full and passes the Phase 7 checks, and the Phase 8 notebooks run.

**Exit criteria**: Either the phase was skipped, with the reason in `conversion_notes.md`, or the check has run,
every finding about the data has been triaged with the user, and the findings that come from the conversion are fixed
and the affected sessions reconverted.

### Step 0: Decide Whether to Run

Skip this phase, and say so in one line, when any of these holds:

- There is no manuscript, preprint, or published paper for this data (`conversion_notes.md`, "Existing Resources").
  A preprint is enough.
- The user cannot provide the paper as a PDF or a text file. `encore check` needs the paper itself, not only its DOI,
  and `tools/fetch_paper.py` truncates long sections, so its output is not a substitute.
- The `claude` command (Claude Code) is not installed and signed in on this machine. Encore runs its agents through it.
  This is the usual case inside NWB GUIDE.

Otherwise, tell the user what the check costs before starting, since it runs for hours and uses their own Claude
account:

> Your data comes with a paper, so before we upload I'd like to run an Encore check. Encore's agents read the paper,
> write down its main findings, and try to reproduce them from the converted NWB files. What usually matters most is
> what they find wrong with the data on the way: wrong units, missing metadata, data the paper relies on that is not
> in the files. A quick check takes one to three hours and counts against the usage of the Claude account that Claude
> Code is signed in to.
>
> <choices>
> <choice>Run the quick check</choice>
> <choice>Run the full check (adds independent verification, several hours more)</choice>
> <choice>Skip it</choice>
> </choices>

If the user skips it, record that in `conversion_notes.md` and go on to Phase 10.

### Step 1: Prepare the Inputs

1. **The paper.** Use the PDF from Phase 1 (`conversion_notes.md`, "Paper PDF"), or ask for it now. Encore reads the
   DOI from the PDF; if it does not show one, pass `--doi`. If the paper describes a larger study than this dataset,
   say so to the user now: findings that rest on data outside the dataset will come back as blocked, which is
   expected.
2. **The data.** Point the check at the folder of full NWB files from Phase 7 Step 7, not the stub folder. Encore
   reads the folder in place and never changes it. The agents are given the NWB files and the paper, not the source data or
   the conversion code, which is the point: the check sees what will be uploaded.
3. **The run directory.** Put it outside the conversion repo. It holds a copy of the paper and a copy of the Encore
   registry, neither of which belongs in the conversion repo.

### Step 2: Run the Check

`encore check` comes from the `encore-science` package and needs Python 3.10 or later and git. Run it with `uvx` so it
does not change the conversion environment:

```bash
uvx --from encore-science encore check /path/to/output/full \
    --paper /path/to/paper.pdf \
    --out ../encore-<lab_name>-<conversion_name>
```

Add `--full` if the user chose the full check, and `--doi <doi>` if the PDF shows no DOI. The command runs for hours,
so run it in the background and check on it with:

```bash
uvx --from encore-science encore status ../encore-<lab_name>-<conversion_name>
```

If it stops (for example, when the account reaches a usage limit), run the same `encore check` command again with
the same `--out`. It continues from the role that stopped.

The agents run inside Claude Code's sandbox, which only lets them write inside the run directory. If the sandbox
cannot start on this machine, `encore check` has a `--no-sandbox` flag. Do not add it yourself; explain to the user
that it lets the agents' commands run unrestricted, and use it only if they agree.

### Step 3: Read the Report

The run writes `report.md` in its directory. It has three parts:

- **Claims**: each finding of the paper that was tested, with its outcome (reproduced, partially reproduced, not
  reproduced, or blocked) and the agent's notes.
- **Findings about the data**: problems the agents found in the files, each with a kind (metadata error, data
  missing, identifier missing, metadata insufficient, selection undocumented, methods unavailable, format error,
  code mismatch, paper inconsistency, other).
- **Where everything is**: the claims file, the notebooks the agent wrote, and its transcripts.

The findings about the data are what this phase is for. The claim outcomes help to read them: a claim that is blocked
or not reproduced because something is missing from the files often points to a stream or a column the conversion
dropped. A "not reproduced" outcome on its own is not evidence that the conversion is wrong. It can come from the
agent's analysis, from methods the paper does not describe fully, or from data the paper used that was never part of
this dataset. Read the agent's notes and notebook before acting on one.

### Step 4: Triage Each Finding

The findings were written by AI agents, not by anyone who knows the data. Expect most of them to hold and some to be
wrong. For each finding, check it yourself against the NWB file (and, where it helps, the source file), then sort it
into one of four groups:

1. **Conversion error**: the conversion wrote a value wrongly, such as a unit, a rate, a scaling factor, an
   electrode location, or a timestamp offset.
2. **Dropped information**: the source has it, but the conversion did not write it, such as a column that was read
   but never added, a stream left out, or sessions that failed without anyone noticing.
3. **Missing from the source**: only the lab can supply it, such as a parameter the paper reports but no file
   contains. Ask the user, and add it to "Open Questions" in `conversion_notes.md` until they answer.
4. **No change to the data**: the finding is about the paper, or it does not hold. Say why in the notes.

Never change data to make a claim reproduce. Fix only what is wrong or missing relative to the source and the lab's
answers. Where a fix needs a fact from the paper, such as a stimulation wavelength, cite the Methods section, and
confirm it with the user when the paper and the source disagree.

Present the triage to the user as a short list, one line per finding with its group and the proposed fix, and agree
on what to change before editing code.

### Step 5: Fix and Reconvert

Fix the findings in groups 1 and 2, and any in group 3 that the user has answered, the same way as in Phase 7: change
the conversion code or metadata, reconvert the affected sessions (as a stub first, then in full), and rerun
`nwbinspector --config dandi` on them. Rerun any Phase 8 notebook that reads a stream you changed.

Rerunning the Encore check is optional and takes as long as the first run. Suggest it to the user only when the fixes
were substantial, such as a new stream or a corrected clock, and run it with a new `--out` directory so the first
report is kept. Once the data is on DANDI, the user can also ask the Encore registry to check the draft with
`encore request DANDI:<dandiset_id> --draft --why "<what changed>"`. That opens a public issue in the registry
under the user's GitHub account and puts the result on the public record, so only run it if the user asks.

### Step 6: Record and Push

Add an "Encore Check" section to `conversion_notes.md`:

```markdown
## Encore Check
- Run: quick | full, <date>, run directory <path>
- Claims: <n> reproduced, <n> partially reproduced, <n> not reproduced, <n> blocked
- Findings about the data:
  | Finding | Group | Action |
  |---------|-------|--------|
  | Spike times in ms, paper and source in s | Conversion error | Fixed in convert_session.py |
  | Laser wavelength not in any file | Missing from the source | Asked the lab |
```

Do not commit the run directory or the report to the conversion repo. In stacked PRs mode, commit each fix on the
branch of the stream it belongs to and carry it up the stack (`knowledge/stacked-prs.md`, "Changing a lower branch").
Otherwise:

```bash
git add -A
git commit -m "Phase 9: fix conversion issues found by the Encore check"
if git remote get-url origin &>/dev/null; then git push; fi
```

> The Encore check is done and the fixes are in. Next we'll upload the data to DANDI.
