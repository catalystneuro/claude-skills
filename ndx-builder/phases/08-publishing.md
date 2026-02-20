## Phase 8: Publishing

**Goal**: Publish the extension to PyPI and submit to the NDX Catalog.

**Entry**: Tests pass, documentation is complete.

**Exit criteria**:
- Extension is published on PyPI
- Extension is submitted to the NDX Catalog (or PR is open)
- GitHub release is created

### Step 1: Prepare for Release

**Verify everything is ready:**

```bash
cd ndx-<name>

# All tests pass
pytest src/pynwb/tests/ -v

# Package builds cleanly
pip install build
python -m build

# Check the built distribution
ls dist/
# Should show: ndx_<name>-0.1.0.tar.gz and ndx_<name>-0.1.0-py3-none-any.whl
```

**Review and update pyproject.toml:**
- `version` is correct
- `description` is final
- `author` and `contact` are correct
- `license` is set
- `requires-python` is appropriate
- Dependencies (`pynwb`, `hdmf`) have minimum version constraints
- **Uncomment and fill in project URLs** (the template generates them commented out):

```toml
[project.urls]
"Homepage" = "https://github.com/<user>/ndx-<name>"
"Bug Tracker" = "https://github.com/<user>/ndx-<name>/issues"
```

### Step 2: Push to GitHub

```bash
# Ensure all changes are committed
git add -A
git status
git commit -m "Prepare v0.1.0 release"

# Create the GitHub repo if it doesn't exist
gh repo create <user>/ndx-<name> --public --description "<description>"

# Push
git remote add origin https://github.com/<user>/ndx-<name>.git 2>/dev/null || true
git push -u origin main
```

### Step 3: Create GitHub Release

```bash
# Tag the release
git tag -a v0.1.0 -m "Initial release v0.1.0"
git push origin v0.1.0

# Create GitHub release
gh release create v0.1.0 \
    --title "v0.1.0" \
    --notes "Initial release of ndx-<name>.

## What's included
- <TypeName>: <brief description>
- <TypeName2>: <brief description>

## Installation
\`\`\`bash
pip install ndx-<name>
\`\`\`"
```

### Step 4: Publish to PyPI

```bash
# Install build and twine if needed
pip install build twine

# Build fresh
rm -rf dist/
python -m build

# Upload to PyPI (requires PyPI account and API token)
twine upload dist/*
```

**First time?** The user needs a PyPI account and API token:
1. Create account at https://pypi.org/account/register/
2. Create API token at https://pypi.org/manage/account/#api-tokens
3. Configure `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-<token>
```

Make sure permissions are restricted: `chmod 600 ~/.pypirc`

If the user provides a token directly, write it to `~/.pypirc` for them.

If `twine upload` fails with an interactive prompt (e.g., in a non-TTY environment),
the `~/.pypirc` file must be configured first.

**Test on TestPyPI first** (optional but recommended):
```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ ndx-<name>
```

### Step 5: Submit to NDX Catalog

The NDX Catalog (https://nwb-extensions.github.io/) is the official registry of
NWB extensions. Each extension gets a "record" repository under the `nwb-extensions`
GitHub organization. A periodic script (`collect-records.py`) scans all
`ndx-*-record` repos and builds the catalog index.

**Create the record repository:**

```bash
# Create the record repo under nwb-extensions org
# (requires write access to nwb-extensions org)
gh api orgs/nwb-extensions/repos \
    --method POST \
    -f name="ndx-<name>-record" \
    -f description="Record for ndx-<name> NWB extension" \
    -f visibility="public"
```

**Clone, populate, and push:**

```bash
# Clone the empty record repo
git clone https://github.com/nwb-extensions/ndx-<name>-record.git
cd ndx-<name>-record
```

Create `ndx-meta.yaml`:

```yaml
name: ndx-<name>
version: 0.1.0
src: https://github.com/<user>/ndx-<name>
pip: https://pypi.org/project/ndx-<name>/
license: BSD-3-Clause
maintainers:
  - <github_username>
```

Create `README.md` with a brief description and link to the source repo.

```bash
git add ndx-meta.yaml README.md
git commit -m "Add ndx-<name> record"
git push origin main
```

The catalog will pick up the new record on its next collection run.

**If you don't have nwb-extensions org access**, ask the user to request access
or to create the record repo manually.

### Step 6: Set Up CI (Optional but Recommended)

Create a GitHub Actions workflow for automated testing:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[test]"
      - run: pytest src/pynwb/tests/ -v
```

Add test dependencies to `pyproject.toml`:
```toml
[project.optional-dependencies]
test = ["pytest", "pytest-cov"]
```

### Common Issues

**`twine upload` fails with "403 Forbidden"**: The package name may already be taken
on PyPI. Check with `pip index versions ndx-<name>`.

**NDX Catalog record not appearing**: The catalog collects records periodically. Make sure:
- The record repo is named `ndx-<name>-record` under `nwb-extensions` org
- `ndx-meta.yaml` has all required fields (name, version, src, pip, license, maintainers)
- The PyPI package exists and is installable
- The source GitHub repo is public

**Version conflicts**: If updating an existing extension, bump the version in
`pyproject.toml` and `create_extension_spec.py` before publishing.
