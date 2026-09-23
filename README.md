# CatalystNeuro Claude Code Skills

Public repository of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for neurophysiology research.

## Installation

### Prerequisites

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started)
2. Ensure you have an active Anthropic API key or Claude Pro/Max subscription

### Adding Skills

Register this repository as a Claude Code plugin marketplace:
```
/plugin marketplace add catalystneuro/claude-skills
```

Then install individual skills:
```
/plugin install analyzing-dandi-datasets@catalystneuro-skills
/plugin install using-nemos@catalystneuro-skills
/plugin install nwb-convert@catalystneuro-skills
/plugin install gin-upload@catalystneuro-skills
```

### Manual Installation (Alternative)

If you prefer to install skills without the marketplace, you can clone this repo and add a skill directly:

```bash
git clone https://github.com/catalystneuro/claude-skills.git ~/claude-skills
```

Then in Claude Code:
```
/skill add ~/claude-skills/nwb-convert
```

### Verifying Installation

After installing a skill, you can verify it's available:
```
/skills
```

This will list all installed skills. You should see the skill name in the list.

## Available Skills

### nwb-convert

Convert neurophysiology data to [NWB](https://www.nwb.org/) format and publish on [DANDI](https://dandiarchive.org/). This skill acts as an expert NWB conversion specialist, guiding you through the entire conversion process:

1. **Experiment Discovery** - Understand your data modalities, recording systems, and file organization
2. **Data Inspection** - Automatically inspect files to identify formats, channels, and structure
3. **Metadata Collection** - Gather required NWB metadata (subject, session, devices, electrodes)
4. **Synchronization** - Analyze and plan temporal alignment across data streams
5. **Code Generation** - Generate a complete, pip-installable conversion repo using [NeuroConv](https://neuroconv.readthedocs.io/)
6. **Testing & Validation** - Run conversions, validate with NWB Inspector, fix issues iteratively
7. **DANDI Upload** - Organize and upload validated NWB files to the DANDI Archive

**Supported modalities:**
- Extracellular electrophysiology (SpikeGLX, OpenEphys, Intan, Blackrock, Neuralynx, Plexon, TDT, Axona)
- Spike sorting (Kilosort, Phy, SpykingCircus, MountainSort, YASS, Combinato)
- Calcium imaging (ScanImage, Scanbox, Bruker, MicroManager, Miniscope, Hamamatsu)
- Segmentation (Suite2p, CaImAn, EXTRACT, CellPose)
- Behavior (DeepLabCut, SLEAP, FicTrac, video, custom formats)
- Intracellular electrophysiology (ABF, WinWCP)

**Usage:**
```
/nwb-convert /path/to/your/data
```

Or simply describe what you want to convert:
- *"I have SpikeGLX recordings with Kilosort sorting and behavioral data from a VR task"*
- *"Convert my two-photon calcium imaging data with Suite2p segmentation to NWB"*
- *"Help me publish my electrophysiology dataset on DANDI"*

**Knowledge base includes:**
- 68 NeuroConv interface specifications
- Canonical conversion repo structure (cookiecutter template)
- Patterns from ~20 real CatalystNeuro conversion repos
- NWB best practices distilled from NWB Inspector

### analyzing-dandi-datasets

Analyze neurophysiology datasets from the [DANDI Archive](https://dandiarchive.org/). Load NWB files with streaming access, use Pynapple for data inspection, and create analysis pipelines for neural phenomena like directional tuning, place cells, and population dynamics.

**Requires:** [neurosift-tools MCP](https://github.com/flatironinstitute/neurosift/blob/main-v2/docs/mcp-neurosift-tools.md#installation-steps)

### using-nemos

Fit Generalized Linear Models (GLMs) to neuroscience data using the [NeMoS](https://nemos.readthedocs.io/) Python package. Covers:

- Basis functions (BSpline, RaisedCosineLog, CyclicBSpline, Eval vs Conv)
- Observation models (Poisson, Gaussian, Gamma, Bernoulli)
- Regularization (Ridge, Lasso, GroupLasso)
- Single-neuron and population GLMs
- Functional connectivity and coupling filter analysis
- Cross-validation and model selection with scikit-learn
- Calcium imaging with Gaussian GLMs

### gin-upload

Add test data to the [gin](https://gin.g-node.org/) git-annex repositories used by NeuroConv and python-neo (`behavior_testing_data`, `ophys_testing_data`, `ephy_testing_data`). These repositories are usually short of examples, so software built against them overfits to the few files that are there. The skill covers:

- Finding more example files for a format, and recording their provenance
- Stubbing a recording down while keeping it internally consistent, and generating synthetic files
- Human subject data
- Licensing: what may be published, and which licenses must travel with the files
- Where data goes, how folders and files are named, and how the README describes them
- Uploading: annexing and locking every file, pushing content before the branch, and fixing files committed as plain git blobs

### using-pynapple

**Moved.** The `using-pynapple` skill now lives in [pynapple-org/claude-skills](https://github.com/pynapple-org/claude-skills) and is maintained there. It is no longer distributed from this repository.

## Usage

After installing a skill, Claude Code will automatically use it when relevant. You can also invoke skills directly with their slash command:

- `/nwb-convert` - Start an NWB conversion workflow
- *"Fit a Poisson GLM with spike history basis"* - triggers `using-nemos`
- *"Find a DANDI dataset with hippocampal place cells"* - triggers `analyzing-dandi-datasets`

## Skill Architecture

Each skill directory contains:
- `SKILL.md` - Main skill definition with frontmatter (name, description, tools) and instructions
- Reference files - Knowledge bases, patterns, and examples that the skill consults

The `nwb-convert` skill is the most complex, with 7 phase-specific instruction files and 4 knowledge base files covering interfaces, repo structure, conversion patterns, and NWB best practices.

## License

MIT
