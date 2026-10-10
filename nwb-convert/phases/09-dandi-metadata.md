## Phase 9: DANDI Metadata

**Goal**: Fill in the Dandiset-level metadata so the Dandiset is citable, findable, and
ready to publish: contributors with ORCIDs and ROR affiliations, a contact person, funders
with award numbers, the associated publication and conversion code, subject terms, keywords,
license, and ethics approval.

**Entry**: The NWB files are uploaded to DANDI (Phase 8). The Dandiset ID and the DANDI
instance (sandbox or archive) are known.

**Exit criteria**: The draft metadata passes validation, or the only remaining errors are
items the user has to supply later (recorded in `conversion_notes.md`). The user has seen
and approved every change.

### Step 1: Load the dandiset-metadata Skill

The metadata work is done by the `dandiset-metadata` skill, maintained by the DANDI project
at https://github.com/dandi/dandi-skills. It is a dependency of this plugin, so in Claude
Code it is normally installed already; invoke it and follow its workflow.

If it is not available (for example inside NWB GUIDE, or when this skill was installed
by copying the folder), fetch it and read its instructions directly:

```bash
SKILLS=~/.cache/dandi-skills
if [ -d "$SKILLS/.git" ]; then git -C "$SKILLS" pull -q; else git clone -q --depth 1 https://github.com/dandi/dandi-skills "$SKILLS"; fi
```

Then read `$SKILLS/dandiset-metadata/SKILL.md` and follow it, treating
`$SKILLS/dandiset-metadata` as the skill directory (`${CLAUDE_SKILL_DIR}` in its commands).
Its helper script needs `requests` and `dandischema`, which the conversion environment
already has through `dandi`.

The user here owns the Dandiset, so the skill's owner mode applies: every field is open,
including the title and description, and the user approves each change before it is saved.
For a sandbox Dandiset, pass `--instance sandbox` to the skill's `fetch`, `audit`, and
`save` commands.

### Step 2: Hand Over What the Conversion Already Knows

Much of what the skill would otherwise ask for was collected in earlier phases. Read
`conversion_notes.md` and supply it instead of asking again:

- **Publication**: the DOI or citation from Phase 1. `tools/fetch_paper.py` can pull the
  full text, whose acknowledgments list funding and award numbers and whose methods usually
  give the IACUC or IRB protocol.
- **Experimenters and lab**: the people named in Phase 3 metadata (`experimenter`, `lab`,
  `institution`). Authors of the paper come from the skill's `import-authors` (use
  `--order paper` so the citation follows the paper); people who collected data but are
  not authors get `dcite:DataCollector`.
- **Brain regions and species**: from Phase 3 and the electrode and imaging-plane locations.
  If regions differ by subject, the skill's `references/asset-metadata.md` covers setting
  them per file.
- **Conversion code**: the conversion repo from Phase 5, as a related resource with relation
  `dcite:IsSupplementedBy` and resource type `dcite:Software`.
- **Data curators**: the people who ran this conversion, with role `dcite:DataCurator` and
  `includeInCitation: false`. Look up their ORCIDs and affiliations with the skill's
  commands like anyone else's.

Ask the user only for what is still missing, typically the contact person's email, the
license, and the ethics protocol if the paper does not state it.

### Step 3: Record What Was Set

After saving, add a short section to `conversion_notes.md` listing what was filled in and
anything left open (for example "contact email pending", "ethics protocol to confirm"),
then commit it.

After Phase 10, add the example notebook to the Dandiset's related resources through the
same skill (relation `dcite:IsSupplementedBy`, resource type `dcite:ComputationalNotebook`).

### Publishing

Publishing is the owner's step, and it is not reversible:

> When the metadata is complete and you're ready to make the dataset permanently citable,
> click "Publish" on the Dandiset page. This creates an immutable version with its own DOI,
> which you can cite in your paper. You can keep uploading and publish new versions later.
