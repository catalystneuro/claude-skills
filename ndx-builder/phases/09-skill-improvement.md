## Phase 9: Skill Improvement

**Goal**: Reflect on the extension-building experience and propose improvements to this skill as a PR.

**Entry**: Extension is published (or at least fully tested and working). You've been through the full workflow and experienced what worked and what didn't.

**Exit criteria**:
- You've reviewed your experience against each phase's instructions
- A PR is open on the skills repo with concrete improvements
- Changes are scoped and well-explained

### Step 1: Reflect on the Build Experience

Think through the entire process you just completed. For each phase, consider:

- **What guidance was missing?** Were there decisions you had to figure out that the skill should have covered?
- **What guidance was wrong or outdated?** Did any instructions lead you astray or reference APIs/patterns that didn't work?
- **What was confusing?** Were there instructions that were ambiguous or could be misinterpreted?
- **What patterns came up that should be documented?** Did you encounter a common scenario (e.g., a specific base type combination, a tricky ObjectMapper case) that would help future builds?

Review `design_notes.md` for any decisions you made that weren't well-supported by the existing knowledge files.

### Step 2: Categorize Improvements

Organize potential changes into categories:

| Category | Examples |
|----------|---------|
| **Phase instructions** | Missing steps, wrong order, incomplete guidance |
| **Knowledge files** | Missing API patterns, outdated examples, new core types |
| **SKILL.md** | Missing critical rules, wrong assumptions, unclear instructions |
| **New knowledge** | Patterns worth documenting that aren't covered anywhere |

Prioritize changes that would have the most impact — focus on things that caused real friction or errors during the build, not cosmetic tweaks.

### Step 3: Clone the Skills Repo and Create a Branch

```bash
# Clone the skills repo (or use existing clone)
cd /tmp
git clone https://github.com/catalystneuro/claude-skills-repo.git claude-skills-repo-pr 2>/dev/null || \
    (cd claude-skills-repo-pr && git fetch origin && git checkout main && git pull)
cd claude-skills-repo-pr

# Create a branch
git checkout -b improve-ndx-builder-from-<extension-name>
```

### Step 4: Make the Changes

Apply your improvements to the skill files. For each change:

1. **Be specific** — edit the exact file and section that needs improvement
2. **Keep changes minimal** — don't rewrite sections that work fine
3. **Add, don't remove** — prefer adding missing guidance over restructuring existing content
4. **Include context** — if adding a new pattern or example, explain when it applies

Common files to update:
- `ndx-builder/phases/*.md` — phase-specific instructions
- `ndx-builder/knowledge/*.md` — API references and examples
- `ndx-builder/SKILL.md` — top-level rules and instructions

### Step 5: Open a PR

```bash
git add ndx-builder/
git commit -m "Improve ndx-builder skill based on ndx-<extension-name> experience"
git push -u origin improve-ndx-builder-from-<extension-name>

gh pr create \
    --title "Improve ndx-builder skill from ndx-<extension-name> build" \
    --body "$(cat <<'EOF'
## Summary
Improvements to the ndx-builder skill based on experience building ndx-<extension-name>.

## Changes
- [List each change with the file and what was improved]

## Context
These changes address friction points encountered during a real extension build.
Each change is something that would have saved time or prevented errors if it
had been in the skill from the start.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Present the PR URL to the user and summarize what you changed and why.

### Guidelines

- **Don't propose changes for one-off issues.** Only suggest improvements for patterns likely to recur across different extensions.
- **Don't bloat the skill.** The skill is already large — only add content that earns its place by preventing real mistakes.
- **Preserve the skill's voice.** Match the existing tone: direct, practical, expert-level. Don't add hedging or filler.
- **Test your claims.** If you're correcting an API pattern, verify the correction is actually right before proposing it.
