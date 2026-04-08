## Phase 1: Spyglass Environment Setup

**Goal**: Set up the Spyglass database and Python environment so the user can run
conversions and insert sessions.

**Entry**: User invokes `/spyglass-convert`.

**Exit criteria**:
- Docker MySQL container is running and accepting connections
- Mamba environment with Spyglass and NeuroConv is active
- `dj_local_conf.json` is written and DataJoint can connect to the database

> I'll start by setting up the Spyglass environment: a MySQL database (via Docker)
> and a Python environment with Spyglass and NeuroConv.
>
> Do you already have Docker installed?

<choices>
<choice>Yes, Docker is installed</choice>
<choice>No, I need to install Docker</choice>
<choice>I already have a Spyglass database running — skip to environment setup</choice>
</choices>

### Step 1: Start the MySQL Database

If the user needs Docker, direct them to https://docs.docker.com/get-docker/.

Start the MySQL container:

```bash
docker run \
  --name spyglass-db \
  -v dj-vol:/var/lib/mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=tutorial \
  -d datajoint/mysql:8.0
```

Verify it started:
```bash
docker ps | grep spyglass-db
```

If the container already exists from a previous run:
```bash
docker start spyglass-db
```

**Ask the user for the connection details** if they are using an existing database
rather than the Docker container above (host, port, username, password).

### Step 2: Set Up the Python Environment

Use `uv` for all package management. All packages should be installed via `uv` —
never use bare `pip install`.

```bash
# Ensure uv is installed
which uv || (curl -LsSf https://astral.sh/uv/install.sh | sh)

# Create venv in the conversion repo (after Step 0 in Phase 2 creates it)
cd <repo_dir>
uv venv
source .venv/bin/activate

# Install base dependencies
uv pip install spyglass-neuro neuroconv pynwb nwbinspector spikeinterface \
    h5py pandas pyyaml jupyter matplotlib pymatreader
```

**Note**: Check the current Spyglass installation guide at
https://lorenfranklab.github.io/spyglass/latest/notebooks/00_Setup/
for any changes to the recommended install method. If any Spyglass dependencies
fail to install via `uv pip install` due to compiled extensions, install them
first via conda and then run `uv pip install --no-build-isolation spyglass-neuro`.

Verify installation:
```bash
python -c "import spyglass; print('Spyglass OK')"
python -c "import neuroconv; print('NeuroConv OK')"
```

### Step 4: Configure DataJoint

Determine where Spyglass should store its data (raw data, analysis results, etc.):

> Spyglass needs a base directory to store raw data copies and analysis outputs.
> Where would you like to store Spyglass data? (e.g., `/data/spyglass` or `~/spyglass_data`)

Create `dj_local_conf.json` in the working directory. Use the Docker container
credentials unless the user has a different setup:

```json
{
  "database.host": "localhost",
  "database.port": 3306,
  "database.user": "root",
  "database.password": "tutorial",
  "database.use_tls": false,
  "custom": {
    "spyglass_base_dir": "<user_chosen_path>",
    "raw_dir": "<user_chosen_path>/raw",
    "analysis_dir": "<user_chosen_path>/analysis"
  }
}
```

Load and save the config (run inside the venv):
```python
import datajoint as dj

dj.conn(use_tls=False)
dj.config.load("dj_local_conf.json")
dj.config.save_local()
```

### Step 5: Test the Connection

```python
import datajoint as dj
import spyglass.common as sgc

dj.config.load("dj_local_conf.json")
print(dj.conn())

# List Spyglass tables as a smoke test
print(sgc.Lab.heading)
```

If the connection fails:
- Check Docker is running: `docker ps`
- Check port 3306 is not occupied by another MySQL instance
- Verify credentials match `dj_local_conf.json`

> Environment setup is complete. The Spyglass database is running and DataJoint
> can connect to it.
>
> Next, let's understand your experiment so we can plan the NWB conversion.
