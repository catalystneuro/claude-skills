---
name: gin-upload
description: >
  How to find, stub, license, organize, document and publish test data to the
  CatalystNeuro and NeuralEnsemble gin git-annex repositories
  (`behavior_testing_data`, `ophys_testing_data`, `ephy_testing_data` on
  gin.g-node.org). Use this skill whenever searching for example data, working
  with human subject data, adding, fixing or verifying data in those
  repositories, running `gin` or `git annex` commands in a clone of them,
  deciding where new data goes inside one, or writing a README there.
---

# gin-upload

These repositories provide examples for software that handles the formats. The
goal of the repositories is to be a good representation of the structural
variation of the formats themselves. A common problem is too few examples,
which this skill aims to address.

## Workflows

**Create a dataset for a new format.** Start with `references/finding_data.md`
and collect several examples, at least three that differ from one another.
Then move iteratively between stubbing, testing a reader or tool, and
organizing the coverage axes, until every identified axis has an example and
another search and testing pass reveals no materially new variation. Check
licenses as candidates become viable. Before publishing, run the final coverage review in
`references/uploading.md` and show its recommendation to the user.

**Add an example to an existing format.** Start with
`references/organizing.md` to understand the existing structure and the
variation the new example represents. Then check `references/licensing.md`,
read `references/stubbing.md` if the file must be reduced or synthesized, and
finish with the upload mechanics in `references/uploading.md`. Name what the
new example adds to the existing coverage. Searching for more data and
reconsidering the complete coverage model are not required.

## References

1. `references/finding_data.md`: finding candidates and recording provenance.
2. `references/stubbing.md`: reducing or generating data, including human data.
3. `references/licensing.md`: deciding what may be published.
4. `references/organizing.md`: folders, names and README conventions.
5. `references/uploading.md`: final coverage review and gin upload mechanics.

Read each relevant reference from start to finish.

Ask the user before `gin upload`, `git push`, or opening a pull request.

## Repositories

| Repository | URL | Used by |
|---|---|---|
| `ephy_testing_data` | `gin.g-node.org/NeuralEnsemble/ephy_testing_data` | python-neo, neuroconv |
| `ophys_testing_data` | `gin.g-node.org/CatalystNeuro/ophys_testing_data` | neuroconv, roiextractors |
| `behavior_testing_data` | `gin.g-node.org/CatalystNeuro/behavior_testing_data` | neuroconv |
