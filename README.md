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
/plugin install using-pynapple@catalystneuro-skills
/plugin install nwb-convert@catalystneuro-skills
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

### using-pynapple

Analyze neurophysiology time series using the [pynapple](https://pynapple.org/) Python package. Covers:

- Core data structures (Ts, Tsd, TsdFrame, TsdTensor, TsGroup, IntervalSet)
- Time series manipulation (restrict, count, smooth, interpolate, bin_average, derivative)
- Metadata management and neuron filtering
- Tuning curves (1D, 2D, n-dimensional)
- Bayesian and template decoding
- Signal processing (filtering, wavelets, Hilbert phase extraction)
- Correlograms and perievent analysis

## Usage

After installing a skill, Claude Code will automatically use it when relevant. You can also invoke skills directly with their slash command:

- `/nwb-convert` - Start an NWB conversion workflow
- *"Load this NWB file and compute head direction tuning curves"* - triggers `using-pynapple`
- *"Fit a Poisson GLM with spike history basis"* - triggers `using-nemos`
- *"Find a DANDI dataset with hippocampal place cells"* - triggers `analyzing-dandi-datasets`

The `using-nemos` and `using-pynapple` skills cross-reference each other since NeMoS workflows typically use pynapple for data preparation.

## Skill Architecture

Each skill directory contains:
- `SKILL.md` - Main skill definition with frontmatter (name, description, tools) and instructions
- Reference files - Knowledge bases, patterns, and examples that the skill consults

The `nwb-convert` skill is the most complex, with 7 phase-specific instruction files and 4 knowledge base files covering interfaces, repo structure, conversion patterns, and NWB best practices.

## License

MIT
