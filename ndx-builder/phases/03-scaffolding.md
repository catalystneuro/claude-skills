## Phase 3: Project Scaffolding

**Goal**: Generate the extension project structure using `ndx-template` (cookiecutter).

**Entry**: You have a finalized design from Phase 2.

**Exit criteria**: A complete, installable project directory with:
- Correct directory structure from ndx-template
- Development installation working (`pip install -e .`)
- All template files in place

### Step 1: Check Prerequisites

```bash
# Check for required tools
python3 -c "import cookiecutter; print('cookiecutter OK')" 2>/dev/null || echo "MISSING: cookiecutter"
python3 -c "import pynwb; print(f'pynwb {pynwb.__version__} OK')" 2>/dev/null || echo "MISSING: pynwb"
```

Install any missing prerequisites:

```bash
pip install cookiecutter pynwb hdmf-docutils
```

**Note**: `hdmf-docutils` is required because the template's post-generation hook
runs `python src/spec/create_extension_spec.py` which imports from it. Without it,
scaffolding will fail at the post-gen step.

### Step 2: Run ndx-template

**If creating a new extension from scratch:**

```bash
cookiecutter gh:nwb-extensions/ndx-template
```

This prompts for:
- `namespace`: Extension name **with `ndx-` prefix** (e.g., `ndx-my-extension`)
  - **Important**: Include the `ndx-` prefix. The template validates this.
- `description`: One-line description
- `author`: Author name
- `email`: Contact email
- `github_user`: GitHub username or org
- `version`: Initial version (default: `0.1.0`)
- `license`: License type — use `BSD-3-Clause` (not `BSD-3`)
- `py_only`: Whether to generate only Python (no MATLAB) — usually `True`

**Pre-fill the answers** based on the design from Phase 2:

```bash
# Non-interactive with a config file
cat > /tmp/ndx-config.yaml << 'EOF'
default_context:
    namespace: "ndx-<name>"
    description: "<from Phase 2>"
    author: "<from user>"
    email: "<from user>"
    github_user: "<from user>"
    version: "0.1.0"
    license: "BSD-3-Clause"
    py_only: "True"
EOF

cookiecutter gh:nwb-extensions/ndx-template --no-input --config-file /tmp/ndx-config.yaml
```

**If the user provided an existing extension repo path**, skip scaffolding and inspect
the existing structure instead.

### Step 3: Inspect Generated Structure

After running cookiecutter, verify the generated structure:

```bash
ls -la ndx-<name>/
```

Expected structure:
```
ndx-<name>/
├── LICENSE.txt
├── MANIFEST.in
├── README.md
├── docs/
│   ├── Makefile
│   └── source/
│       ├── conf.py
│       ├── credits.rst
│       ├── description.rst
│       ├── format.rst
│       ├── index.rst
│       └── release_notes.rst
├── pyproject.toml
├── src/
│   ├── matnwb/                    # Only if py_only=False
│   ├── pynwb/
│   │   ├── ndx_<name>/
│   │   │   ├── __init__.py
│   │   │   └── testing/
│   │   │       ├── __init__.py
│   │   │       └── mock.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_<name>.py
│   └── spec/
│       └── create_extension_spec.py
└── spec/                          # Generated YAML (initially empty or template)
    ├── ndx-<name>.extensions.yaml
    └── ndx-<name>.namespace.yaml
```

### Step 4: Install in Development Mode

```bash
cd ndx-<name>
pip install -e .
```

Verify the installation:

```bash
python3 -c "import ndx_<name_underscored>; print('Import OK')"
```

If the import fails, check:
- The namespace YAML files exist in `spec/`
- `pyproject.toml` includes the spec files in the package data
- The `__init__.py` correctly loads the namespace

### Step 5: Review pyproject.toml

The generated `pyproject.toml` should have:

```toml
[project]
name = "ndx-<name>"
version = "0.1.0"
description = "..."
requires-python = ">=3.9"
license = { text = "BSD-3-Clause" }
dependencies = [
    "pynwb>=2.5.0",
    "hdmf>=3.10.0",
]
```

Verify that:
- The `name` field matches the extension name
- `pynwb` and `hdmf` are listed as dependencies
- The build system is configured (typically `hatchling`)
- Package data includes `.yaml` files from `spec/`

### Step 6: Initialize Git

If not already a git repo:

```bash
cd ndx-<name>
git init
git add -A
git commit -m "Initial scaffold from ndx-template"
```

### Common Issues

**`cookiecutter` not found**: Install with `pip install cookiecutter`

**Template download fails**: Clone manually:
```bash
git clone https://github.com/nwb-extensions/ndx-template.git /tmp/ndx-template
cookiecutter /tmp/ndx-template
```

**Import fails after install**: The spec YAML files need to be generated (Phase 4)
before the package can be imported. This is expected at this stage.

**Python version mismatch**: ndx-template requires Python 3.9+. Check `python3 --version`.
