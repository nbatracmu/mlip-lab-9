# Lab Instructions

> **Before starting**: Make sure you have completed the [Setup section in the README](README.md#setup) and have a working pipeline (Deliverable 1).

---

## Part 1: DVC — Declarative Pipeline Management

In this part, you will explicitly declare your pipeline using DVC. Every stage, dependency, parameter, and output must be defined by you in configuration files.

### 1A: Initialize DVC and Track Data (~20 min)

**Initialize DVC** in your repository:

```bash
dvc init
git add .dvc .dvcignore
git commit -m "Initialize DVC"
```

**Configure a local remote** for storage:

```bash
dvc remote add -d local_storage /tmp/dvc-storage
git add .dvc/config
git commit -m "Configure DVC remote storage"
```

**Track the raw dataset** with DVC:

```bash
dvc add data/raw/data.csv
git add data/raw/data.csv.dvc data/raw/.gitignore
git commit -m "Track raw dataset with DVC"
dvc push
```

Examine the `.dvc` file that was created. Notice it contains a hash of the file contents, not the data itself.

**Create a new data version** using the augmentation script:

```bash
python3 scripts/augment_data.py
dvc add data/raw/data.csv
git add data/raw/data.csv.dvc
git commit -m "Augmented dataset with synthetic samples"
dvc push
```

**Practice switching between versions**:

```bash
git log --oneline                    # find the commit before augmentation
git checkout <commit-hash> -- data/raw/data.csv.dvc
dvc checkout                         # restores the original data file
wc -l data/raw/data.csv             # verify row count changed

git checkout HEAD -- data/raw/data.csv.dvc
dvc checkout                         # back to augmented version
wc -l data/raw/data.csv             # verify row count
```

Think about what just happened: Git tracked a small pointer file, while DVC managed the actual data. This is how teams handle large datasets without bloating their Git repository.

### 1B: Build the DVC Pipeline (~30 min)

Now instead of tracking outputs manually, you will define a **declarative pipeline** that describes the full workflow.

If you tracked the model with `dvc add` earlier, remove that tracking first:

```bash
dvc remove models/classifier.pkl.dvc 2>/dev/null
```

**Create `dvc.yaml`** based on `dvc.yaml.template`. Read each script to understand what files it reads and writes, then declare those as dependencies and outputs. The template has the structure and hints you need.

After creating `dvc.yaml`, **run the pipeline**:

```bash
dvc repro
```

**Visualize the dependency graph**:

```bash
dvc dag
```

You should see a three-stage DAG showing the flow from preprocess → train → evaluate.

**Test the caching**: change `n_estimators` in `params.yaml` (e.g., from 100 to 200), then:

```bash
dvc repro
```

Notice that `preprocess` is *not* re-run — only `train` and `evaluate` re-run, because DVC knows the preprocessing stage's dependencies haven't changed.

```bash
git add .
git commit -m "DVC pipeline with updated hyperparameters"
```

### 1C: Experiment Tracking (~25 min)

DVC can run and compare multiple experiments without manually editing files and committing each time.

**Run at least 3 experiments** with different hyperparameters:

```bash
dvc exp run -S train.n_estimators=50 -S train.max_depth=5
dvc exp run -S train.n_estimators=200 -S train.max_depth=15
dvc exp run -S train.n_estimators=300 -S train.max_depth=20
```

**Compare results**:

```bash
dvc exp show
```

**Apply the best experiment** to your workspace:

```bash
dvc exp apply <best-experiment-name>
git add .
git commit -m "Apply best experiment"
```

**Push experiments**:

```bash
dvc push
```

Think about: DVC experiment tracking gives you a structured table of runs with their parameters and metrics. How does this compare to experiment tracking tools like Weights & Biases?

> **Checkpoint (Deliverable 2)**: Show the TA:
> - Your `dvc dag` output
> - The `dvc exp show` table with 3+ experiments
> - That changing a parameter only re-runs affected stages
> - Explain: why can't Git alone handle this? How does DVC decide what to re-run?

---

## Part 2: Roar — Implicit Lineage Tracking

Now you will run the **same pipeline** using Roar. The key difference: you will not write any configuration file. Roar infers the pipeline by observing what your code actually reads and writes.

### 2A: Initialize Roar (~10 min)

**Initialize Roar** in the same repository:

```bash
roar init
```

This creates a `.roar/` directory with a local SQLite database. No remote configuration, no YAML files.

When prompted, let Roar add `.roar/` to your `.gitignore`.

### 2B: Run the Pipeline with Observation (~15 min)

Run each pipeline step, prefixed with `roar run`:

```bash
roar run python3 scripts/preprocess.py
roar run python3 scripts/train.py
roar run python3 scripts/evaluate.py
```

That is the entire setup. No `dvc.yaml` equivalent was needed.

> **Important**: Use `python3` (not `python`) in the `roar run` command. On macOS, `python` may not exist or may point to a SIP-protected binary, causing Roar's tracer to fail. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you get errors here.

**Inspect the auto-inferred DAG**:

```bash
roar dag
```

Compare this DAG to your `dvc dag` output from Part 1. Roar inferred the dependencies by watching file I/O — it saw that `train.py` read `data/processed/train.csv` (produced by `preprocess.py`) and wrote `models/classifier.pkl` (read by `evaluate.py`).

**Inspect a specific job** to see what Roar captured:

```bash
roar show @1
```

Notice it recorded the exact command, git commit, input/output files with content hashes, and runtime environment.

### 2C: Make a Change and Trace the Impact (~15 min)

Now change something and observe how the lineage updates.

**Augment the dataset**:

```bash
roar run python3 scripts/augment_data.py
```

**Re-run the pipeline** with the modified data:

```bash
roar run python3 scripts/preprocess.py
roar run python3 scripts/train.py
roar run python3 scripts/evaluate.py
```

**Inspect the updated DAG**:

```bash
roar dag
```

Notice how the DAG now reflects the current state — the latest runs with the augmented data. Roar keeps history but `roar dag` shows what is true *now*.

Think about the difference: with DVC, you ran `dvc repro` and it decided what to re-run. With Roar, *you* decided what to re-run, and Roar just recorded what happened. DVC is prescriptive; Roar is descriptive.

### 2D: Register and Browse Lineage on GLaaS (~15 min)

Roar can publish lineage to GLaaS (Global Lineage as a Service) so artifacts are globally identifiable by their content hash.

**Authenticate with GLaaS** (free, uses your GitHub account):

```bash
roar auth register
```

This prints your public key. Go to [glaas.ai](https://glaas.ai/), click "Sign in with GitHub," then paste your key under "SSH key" in your profile.

Test the connection:

```bash
roar auth test
```

**Register your model artifact**:

```bash
roar register models/classifier.pkl
```

Roar uploads the *lineage* (not the file itself) and prints a reproduction command with the artifact hash.

**Browse the lineage** at [glaas.ai](https://glaas.ai/):

1. Search for your artifact hash
2. Click through: artifact → producing job → full DAG
3. See the complete trail: which data, which code, which commit produced this model

**Test reproducibility** (optional but recommended):

```bash
mkdir /tmp/reproduce-test && cd /tmp/reproduce-test
roar reproduce <artifact-hash>
```

Roar shows you the recipe — the exact steps needed to recreate the artifact from scratch.

> **Checkpoint (Deliverable 3)**: Show the TA:
> - Your `roar dag` output (before and after the change)
> - The registered artifact on glaas.ai — navigate the lineage in the browser
> - Explain: how did Roar know that `train.py` depends on `preprocess.py`'s output, without you declaring it?

---

## Part 3: Compare and Reflect

You have now used both tools on the same pipeline. Answer the following questions (write 2-4 sentences each):

### Reflection Questions

**Q1 — Setup and configuration**:
Compare the setup effort for DVC vs. Roar. What did you have to configure explicitly for DVC that Roar handled automatically? What did DVC give you that Roar did not?

**Q2 — The DAGs**:
Look at both DAG outputs side by side. Do they show the same pipeline structure? Are there any differences in what each tool captured? Which was easier to understand?

**Q3 — Handling changes**:
When you changed a hyperparameter (DVC) or augmented the dataset (Roar), how did each tool respond? With DVC, what determined which stages re-ran? With Roar, who decided what to re-run?

**Q4 — Reproducibility**:
DVC uses `dvc.lock` to record exact dependency versions. Roar uses content hashes and `roar reproduce`. What are the trade-offs? Which gives you more confidence that a result can be recreated?

**Q5 — Team collaboration**:
Imagine a new teammate joins your project next month. With DVC, they can read `dvc.yaml` in the Git repo. With Roar, they can look up artifact lineage on GLaaS. Which gives a clearer picture of the pipeline? Could you use both tools together — and if so, how?

**Q6 — Your project**:
For your team's course project, which approach (or combination) would be more useful? Consider your data sources, pipeline complexity, and how your team collaborates.

> **Checkpoint (Deliverable 4)**: Share your written answers with the TA and be prepared to discuss.
