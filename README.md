# CatalystNeuro Claude Code Skills

Public repository of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for neurophysiology research.

## Installation

Register this repository as a Claude Code plugin marketplace:
```
/plugin marketplace add catalystneuro/claude-skills
```

Then install individual skills:
```
/plugin install analyzing-dandi-datasets@catalystneuro-skills
/plugin install using-nemos@catalystneuro-skills
/plugin install using-pynapple@catalystneuro-skills
```

## Available Skills

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

After installing a skill, Claude Code will automatically use it when relevant. For example:

- *"Load this NWB file and compute head direction tuning curves"* - triggers `using-pynapple`
- *"Fit a Poisson GLM with spike history basis"* - triggers `using-nemos`
- *"Find a DANDI dataset with hippocampal place cells"* - triggers `analyzing-dandi-datasets`

The `using-nemos` and `using-pynapple` skills cross-reference each other since NeMoS workflows typically use pynapple for data preparation.

## License

MIT
