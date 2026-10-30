## Phase 12: Wrap-Up

**Goal**: Archive the conversation that produced the conversion in the conversion repo.

**Entry**: Phase 11 is complete.

**Exit criteria**: The conversation is committed to the repo, or the user declined and the copy is deleted.

### Save Conversation History

Save the Claude Code conversation that produced this conversion into the repo. This
captures every decision, data inspection, question, and code generation step for
full reproducibility.

Claude Code names each transcript after its session ID and exports that ID to shell
commands as `CLAUDE_CODE_SESSION_ID`. Copy that file and scan the copy for secrets:

```bash
CONVERSATION=$(ls ~/.claude/projects/*/"$CLAUDE_CODE_SESSION_ID".jsonl)
mkdir -p .claude
cp "$CONVERSATION" .claude/conversation.jsonl

# Values of credentials set in this shell
for name in DANDI_API_KEY DANDI_SANDBOX_API_KEY GITHUB_TOKEN GH_TOKEN; do
    value=$(printenv "$name")
    if [ -n "$value" ] && grep -qF "$value" .claude/conversation.jsonl; then
        echo "FOUND value of $name"
    fi
done

# Common credential patterns, cut to 24 characters so the scan does not print a whole secret
grep -oE 'DANDI(_SANDBOX)?_API_KEY=[^ "\\]+|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|[Pp]assword[=:] *[^ "\\]+' \
    .claude/conversation.jsonl | cut -c1-24 | sort | uniq -c
```

Review every match. Placeholders such as `DANDI_API_KEY=<key>` from the skill text are
harmless. If a real key, token, or password appears, delete `.claude/conversation.jsonl`,
do not commit it, and tell the user which credential appeared so they can revoke it.

If the scan is clean, ask the user before committing. Tell them the file holds the whole
session, including tool outputs, local paths, and excerpts of their data, and, if the repo
has a remote, that it will be pushed there (say whether that repo is public). Commit only
after they agree:

```bash
git add .claude/conversation.jsonl
git commit -m "Save Claude Code conversation history"
if git remote get-url origin &>/dev/null; then git push; fi
```

If they decline, delete `.claude/conversation.jsonl`.

The conversation file is a JSONL containing the full exchange between the user and Claude
Code, including tool calls, file reads, and data inspection outputs. It can be replayed
to understand exactly how the conversion was built.
