---
name: analyzing-dandi-datasets
description: Use this skill when analyzing neurophysiology datasets from the DANDI Archive, including discovering relevant datasets, loading NWB files with streaming access (LINDI/remfile), using Pynapple for data inspection and analysis, and creating analysis pipelines for neural phenomena like directional tuning, place cells, time series analysis, or population dynamics. Emphasizes proper data handling, visualization, and reproducible workflows.
---

# Analyzing DANDI Archive Neurophysiology Datasets

This skill guides you through discovering, loading, and analyzing neurophysiology datasets from the DANDI Archive using modern Python tools (Pynapple, LINDI, NWB) and proper scientific workflows.

## Core Principles

- **CRITICAL - Use Real Data ONLY**:
  - ALWAYS work with actual DANDI Archive datasets
  - NEVER use synthetic, simulated, or generated data under ANY circumstances
  - If a dataset has issues, find a different DANDI dataset - do NOT create simulations
  - If no suitable dataset exists, inform the user and STOP - do NOT proceed with synthetic data
  - This is a hard requirement with NO exceptions
- **Streaming Access**: Use LINDI or remfile with local caching instead of full downloads
- **Let Errors Surface**: Do NOT use try/except blocks during development - errors should be visible for proper diagnosis
- **Validate Early**: Inspect and visualize each data stream as it's loaded before analyzing
- **Progressive Execution**: Run code frequently, generate intermediate plots for validation
- **Verify Visuals**: ALWAYS read generated plots as images using the Read tool to check for overlapping elements, cramped layouts, or readability issues before proceeding
- **Scale Beyond Single Sessions**: After prototyping on one session, extend analysis to multiple sessions for robust population-level conclusions

## Workflow Stages

### 1. Dataset Discovery and Setup

1. **Find Datasets**: Use the neurosift-tools MCP to search DANDI Archive for datasets relevant to the requested neural phenomenon
2. **Create Analysis Structure**:
   - Create a dedicated folder with a descriptive name (e.g., `hippocampal_place_cells_analysis/`)
   - Write a README.md documenting the analysis goal, dataset details, and approach
3. **Inspect Dataset**: Use Pynapple to explore NWB file contents and structure (see `./nwb-data-access-patterns.md` for examples)
4. **Find Similar Analyses**: Use repo-search MCP to locate relevant Pynapple functions and examples
5. **Install Dependencies**: Set up required packages (pynapple, lindi, remfile, pynwb, h5py, tqdm, matplotlib)

**Data Access Strategy**:
- For `.lindi.json` files: Use LINDI with local caching
- For direct S3 URLs: Use remfile with disk caching
- If a dataset lacks required data types, search for alternatives before proceeding

**CRITICAL - When Data Issues Occur**:
- If data alignment fails, try different datasets or different sessions within the same dandiset
- If timestamps don't match, investigate the NWB structure more carefully
- If no suitable data is found after thorough search, inform the user and STOP
- NEVER EVER create synthetic/simulated data as a workaround
- Ask the user if they want to try a different neural phenomenon that has better data available

### 2. Prototype with Single Session

Start with one recording session to develop the analysis pipeline:

1. **Load Data**: Use appropriate method from `./nwb-data-access-patterns.md`
2. **Inspect Structure**: Print NWB object to see available data streams
3. **Visualize Raw Data**: Create time series plots of neural activity before any processing
4. **Validate Data Quality**: Check for NaNs, missing data, edge cases

### 3. Scale to Multiple Sessions

After validating the analysis on a single session, extend to multiple sessions:

**Selection Strategy**:
- Use multiple sessions from the same dandiset for consistency
- Check that all sessions contain the required data types
- Document any sessions excluded due to quality issues

**Implementation Pattern**:
```python
# Loop over multiple sessions
session_urls = [url1, url2, url3, ...]  # or use DANDI API to get all sessions
results_per_session = []

for session_url in tqdm(session_urls, desc="Processing sessions"):
    nwb = load_session(session_url)
    # Run your analysis pipeline
    results = analyze_session(nwb)
    results_per_session.append(results)

# Aggregate results
pooled_data = aggregate_across_sessions(results_per_session)
```

**Aggregation Strategies**:
- **Pool all units**: Combine units from all sessions (increases sample size)
- **Session-level statistics**: Compute statistics per session, then average
- **Mixed effects**: Use session as a random effect if testing hypotheses
- **Longitudinal**: Track changes across sessions if temporal order matters

**Cross-Session Visualizations**:
- Distribution plots comparing metrics across sessions
- Session-by-session summary statistics
- Population averages with session-level error bars
- Correlation between session characteristics and neural metrics

### 4. Implement Modular Analysis Pipeline

Create separate, well-organized analysis components:

**File Structure**:
- `01_load_data.py` - Data loading and initial inspection
- `02_preprocess.py` - Preprocessing and quality checks
- `03_analyze_[phenomenon].py` - Core analysis (e.g., `03_analyze_directional_tuning.py`)
- `04_visualize.py` - Comprehensive visualization suite

**Analysis Guidelines**:
- Use Pynapple for both data access AND analysis computations
- Handle data issues as they arise (don't assume clean data)
- Include progress bars (tqdm) for operations taking >10 seconds
- Save intermediate results with descriptive filenames

### 5. Visualization Requirements

Generate comprehensive figures:

- **Raw Data**: Time series plots showing neural activity and behavior
- **Analysis-Specific**: Tuning curves, raster plots, correlation matrices, PSTHs, etc.
- **Statistical Summaries**: Distribution plots, population statistics
- **Quality Checks**: Data quality metrics and validation plots

**CRITICAL - Visual Quality Verification**:
After generating ANY plot/figure, you MUST:
1. **Read the image file** using the Read tool to visually inspect it
2. **Check for visual issues**:
   - Overlapping text labels, titles, or legends
   - Subplot titles overlapping with plot elements (especially in polar plots)
   - Axis labels that are cut off or obscured
   - Legend boxes that cover important data
   - Cramped layouts where elements are too close together
   - Unreadable text due to small font sizes or poor contrast
3. **Fix any issues immediately** by adjusting:
   - `plt.tight_layout()` parameters
   - GridSpec `hspace` and `wspace` values
   - Subplot title `pad` parameter
   - Font sizes for readability
   - Legend positions (`bbox_to_anchor`, `loc`)
   - Figure size (`figsize`)
4. **Re-generate and re-verify** the plot until all visual issues are resolved

This verification step is NOT optional - it ensures professional-quality figures suitable for presentations and publications.

### 6. Create Reproducible Output

**Final Deliverables**:
1. **Consolidated Script**: Create a single `.py` file using jupytext format with markdown cells
2. **Documentation**: Include clear explanations of the phenomenon being demonstrated
3. **Jupyter Notebook**: Convert to `.ipynb` using nbconvert for easy sharing
4. **Ensure Reproducibility**: Final script should run end-to-end without manual intervention

**Example Final Script Structure**:
```python
# %% [markdown]
# # Analysis Title
# Description of the phenomenon and approach

# %% [markdown]
# ## Setup and Data Loading

# %%
import pynapple as nap
import lindi
# ... loading code ...

# %% [markdown]
# ## Analysis

# %%
# ... analysis code ...

# %% [markdown]
# ## Results
# Interpretation and findings
```

## Common Analysis Patterns

### Directional Tuning
- Extract spike times during movement planning or execution
- Compute firing rates for different movement directions
- Create polar tuning curves, test significance with ANOVA
- Identify preferred directions and tuning strength

### Hippocampal Place Cells
- Analyze spatial firing patterns during navigation
- Compute place fields, spatial information, and sparsity
- Create occupancy maps and firing rate maps
- Identify place cells using spatial information criteria

### Time Series Analysis
- Align neural activity to behavioral events
- Compute PSTHs (peri-stimulus time histograms)
- Analyze trial-to-trial variability
- Create raster plots and spike density functions

### Population Dynamics
- Multi-neuron correlation analysis
- Dimensionality reduction (PCA, t-SNE on firing rates)
- Population vector analysis
- Network-level patterns and synchrony

## Best Practices

- **Real Data Only**: NEVER create or use synthetic/simulated data - this is non-negotiable
- **Data Validation**: Always inspect data before and during analysis
- **Incremental Development**: Build the pipeline step by step, validating each stage
- **Visual Quality Control**: Read every generated plot as an image and verify there are no overlapping elements, cut-off labels, or layout issues
- **Clear Naming**: Use descriptive variable names and file names
- **Document Assumptions**: Note any assumptions about data structure or quality
- **Version Control**: Consider using git for analysis code
- **Share Findings**: Include interpretation and scientific context in final outputs

## What To Do When You Can't Find Suitable Data

If you exhaust all options and cannot find suitable real data from DANDI:

1. **Search thoroughly first**:
   - Try multiple search terms
   - Check related dandisets
   - Look at different brain regions or species
   - Try semantic search with various queries

2. **If no data found**:
   - Inform the user clearly that no suitable DANDI data is available
   - Suggest alternative neural phenomena that have good data
   - Ask if they want to try a different analysis
   - STOP - do not create synthetic data

3. **NEVER**:
   - Create simulated data "for demonstration"
   - Generate synthetic spike trains
   - Use "realistic" artificial data
   - Proceed with any non-DANDI data source

## Reference Files

- `./nwb-data-access-patterns.md` - Code examples for loading NWB files with LINDI and remfile
