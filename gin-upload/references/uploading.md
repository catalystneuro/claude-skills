# Uploading to gin

## Before publishing a dataset for a new format

If the files were stubbed, check that each is a proper stub: it preserves its
claimed coverage axes, remains internally consistent, and opens with readers
that make reasonable assumptions about the format. If you are building a
reader or tool, test the prototype against every proposed example and check
that it handles each claimed axis of variation.

Review the final set for examples that add no distinct structural or
reader-relevant variation. Then run a best-of-five design pass: propose five
ways to define and organize the observed axes, compare their advantages and
disadvantages against the files and reader behavior, and select the strongest
one.

Show the selected model and recommended upload set to the user, explain the
reasoning behind the choice, and include the second-best model, the rejected
alternatives, and any redundant examples. Do not continue to a remote write
until the user chooses.

Before modifying a repository clone, check its top-level `README.md` for
repository-specific contribution and pull-request conventions. Use this
reference for the annex and upload mechanics.

Ask the user before anything that writes to the remote: `gin upload`,
`git push`, or opening a pull request. For a new format dataset, ask after the
final coverage review above.

## Prerequisite: an SSH key registered with gin

gin is pushed to over SSH, so your gin account must know a public SSH key that
your machine holds. A key registered with GitHub is not automatically accepted
by gin; each host keeps its own list. Check before starting, since otherwise the
failure only shows up at upload time:

```bash
ssh -T git@gin.g-node.org
```

- `Hi there, You've successfully authenticated, but GIN does not provide shell
  access.` means you are set.
- `Permission denied (publickey)` means gin does not know any key you hold:
  1. Print your public key: `ssh-add -L`, or `cat ~/.ssh/<key>.pub`.
  2. On gin.g-node.org, open your avatar, **Settings**, **SSH / GPG Keys**,
     **Add Key**, paste the whole line and save.
  3. Run the check again.

Adding the key is the account owner's action. If `ssh-add -L` prints nothing,
a key has to be created or loaded in a terminal first.

## One-time clone setup

```bash
gin login
gin get CatalystNeuro/behavior_testing_data     # or the repository you need
cd behavior_testing_data
git config --unset annex.addunlocked            # see below
```

gin-cli writes `annex.addunlocked = true` into the `.git/config` of every clone
it makes. With it, `git annex add` stores files as unlocked pointers (mode
`100644`), which look like ordinary git files in a tree listing. A scan that
only reads tree modes then misses them, and content referenced only by
unlocked pointers has been lost this way when branches were deleted. Locked
files (mode `120000`, a symlink whose target contains the annex key) are immune.

- The setting is per clone. Nothing can be changed on gin to fix it for others.
- `git annex config --set annex.addunlocked false` does not override a local
  `true`.
- Plain `git add` always adds unlocked. Use `git annex add`.

Check that new adds land locked:

```bash
echo x > probe.bin && git annex add probe.bin
git ls-files -s probe.bin       # expect mode 120000
git rm -q --cached probe.bin && rm probe.bin
```

## Adding data

```bash
git switch -c <branch>
# copy the files into place
git annex add <path>             # mandatory: gin commit never annexes
gin commit -m "<message>" <path>
gin lock <path>                  # required in every repository
```

`gin commit` ignores `annex.largefiles` and `.gitattributes`: whatever it
commits without a prior `git annex add` lands in git as a plain blob, which
every clone carries forever and which cannot be dropped. There is no `gin add`
subcommand.

Check that every data file is locked. Mode `120000` means an annex symlink, so
this one command covers both annexed and locked. It should print only README,
LICENSE and other text files:

```bash
git ls-tree -r HEAD <path> | awk '$1 != "120000" {print $4}'
```

As a backup, the symlink target must contain the annex key:

```bash
git cat-file -p HEAD:<file>      # prints a path containing /annex/objects/MD5E-...
```

Files copied from an exFAT or NTFS drive come in with mode 755. Normalise them
before adding: `find <path> -type f -exec chmod 644 {} +`.

## Pushing: content first, then the branch

`gin upload` pushes the branch and transfers annex content as two separate
steps, and the first can succeed while the second fails. The remote then holds
pointers to content it does not have, and fresh clones cannot fetch those
files. Push in this order instead, so a pointer never reaches the remote before
its content:

```bash
git annex copy --to origin <path>          # content
git push -u origin <branch>                # then the branch
git push origin git-annex                  # and the location log
```

Verify:

```bash
git annex find --in=here --not --in=origin <path> | wc -l    # expect 0
git ls-tree -r origin/<branch> <path> | awk '$1 != "120000" {print $4}'   # only text files
git annex whereis <file>                                     # origin among the copies
```

If you use `gin upload` instead, scope it: `gin upload <path>`. A bare
`gin upload` or `gin upload .` transfers every annexed file present in your
clone, including other people's datasets. `gin upload` can also make its own
commit that turns an annex pointer back into a blob, so run the checks again
afterwards.

Then open a pull request to `master` on the gin web interface
(`https://gin.g-node.org/<org>/<repo>/compare/master...<branch>`). Do not merge
your own pull request.

If you amend a commit after pushing, re-push with
`git push --force-with-lease origin <branch>`. A README-only change needs no new
content upload.

## Fixing files already committed as plain blobs

Older data in these repositories was sometimes committed as plain git blobs.
That is a defect, not a model to follow. To convert such files:

```bash
git rm --cached -- <paths>
git annex add --force-large -- <paths>
git update-index --chmod=+x -- <paths that were 100755>   # git annex add drops the executable bit
```

`--force-large` is needed: `git annex add` has been seen to keep files in git
even when `git check-attr annex.largefiles` says they should be annexed. Check
each file with `git cat-file -p HEAD:<path>` afterwards.

If the blob is only in commits on your branch, squash or rebase it away before
merging, so it never becomes part of `master`'s history. Once it is on
`master`, every clone carries it. Re-adding a blob whose exact bytes are already
in `master`'s history costs nothing, since git stores content once; check with
`git rev-list --objects origin/master | grep <blob-sha>`.

## Repository-specific annex rules

- `ophys_testing_data` annexes binary files and all `*.csv` and `*.tsv`
  (`* annex.largefiles=((mimeencoding=binary)and(largerthan=0))`); `.md` and
  `.txt` stay in git. The rules apply only to files added after they were
  introduced.
- `ephy_testing_data` annexes everything except `LICENSE*`, `README*`,
  `config*`, `*.py` and `.git*`.
- `behavior_testing_data` annexes everything except `LICENSE*`, `README*`,
  `config*` and `.git*`.

### Text-looking binaries

git-annex decides whether a file is binary from its first bytes. A Bruker /
PrairieView OME-TIFF starts with embedded XML, so in `ophys_testing_data` it is
treated as text and committed to git. Force it into the annex:

```bash
git rm --cached -q <file.ome.tif>
git -c annex.largefiles=anything annex add <file.ome.tif>
```
