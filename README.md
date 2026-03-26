# Lab 9 : Data & Pipeline Versioning — DVC and Roar

## Part 3: Compare and Reflect

You have now used both tools on the same pipeline. Here is the completed summary table and reflection answers based on hands-on experimentation with both DVC and Roar.

### Summary Table

| | DVC | Roar |
|---|---|---|
| **Philosophy** | Declarative: You explicitly define the pipeline in `dvc.yaml` with stages, dependencies, and outputs. You tell DVC what your pipeline looks like, and DVC enforces it. | Implicit: Roar observes file I/O as your code runs and automatically infers the dependency graph. You just run your code; Roar figures out the pipeline. |
| **Config required** | `dvc.yaml` (pipeline definition), `dvc.lock` (execution record), `params.yaml` (hyperparameters), `.dvc/config` (remote storage). Explicit declarative configuration. | No pipeline config files. Only `.roar/` directory (SQLite database) created by `roar init`. Everything is implicit. |
| **How is the DAG defined?** | Explicitly written in `dvc.yaml`; each stage lists `deps`, `params`, `outs`, and `metrics`. The DAG is human-readable and version-controlled. | Auto-inferred from file I/O tracing during `roar run`. Roar watches which files each job reads/writes and builds the DAG from observed dependencies. |
| **What happens on re-run?** | `dvc repro` checks dependencies and file hashes in `dvc.lock`. Only re-runs stages whose dependencies changed. Unused (cached) stages are skipped, saving time. | `roar run` always executes the command you give it. Roar keeps a history of all runs but doesn't auto-skip stages. You decide what to re-run. |
| **How are artifacts versioned?** | By content hash (MD5). `dvc add` creates `.dvc` files with hashes. `dvc push` backs up data to remote storage (e.g., S3, local). `dvc checkout` restores files by hash. | By content hash (SHA-256). `roar run` records input/output hashes. `roar register` publishes artifacts to GLaaS (Global Lineage as a Service) for discoverability. No backup storage by default. |
| **Reproducibility mechanism** | `dvc.lock` records the exact parameters, data hashes, and outputs from each run. `dvc repro` with `dvc.lock` guarantees the same conditions. Git commit + `dvc.lock` + `dvc push` = full reproducibility. | `roar show @N` displays exact command, Git commit, input/output hashes, and timestamp. Reproducibility requires manually re-running the same command at the recorded Git commit. |
| **Collaboration model** | Share `dvc.yaml` + Git commits + `dvc.lock`. Team members clone repo, run `dvc pull` to fetch data from remote. Pipeline is explicit and human-reviewable. | Share artifacts via GLaaS by content hash (globally identifiable). Git repo is optional. Artifact lineage is accessible via web interface (`glaas.ai`) without cloning. |
| **Platform support** | Windows (native), macOS (native), Linux (native). Works everywhere with standard Python. | macOS (requires non-Apple Python to avoid SIP restrictions), Linux (native), Windows (requires WSL2). Platform limitations due to file I/O tracing requirements. |

---

### Reflection Questions & Answers

#### **Q1 — Setup and configuration**

*Compare the setup effort for DVC vs. Roar. What did you have to configure explicitly for DVC that Roar handled automatically? What did DVC give you that Roar did not?*

**Answer:**

DVC required significantly more explicit configuration:
- **DVC setup**: Wrote `dvc.yaml` (pipeline definition), ran `dvc init`, configured remote storage with `dvc remote add`, manually tracked data with `dvc add`, committed `.dvc` files and `.dvcignore`.
- **Roar setup**: Single command `roar init`, then just prefixed each script with `roar run`. Roar automatically inferred dependencies by watching file I/O.

**What DVC provided that Roar did not:**
- Automatic experiment tracking with `dvc exp run` — run multiple parameter configurations without editing files and re-committing
- Selective stage re-execution — DVC skips stages whose dependencies haven't changed, saving compute time
- Integrated metrics comparison — `dvc exp show` displays all experiments in a table for instant comparison
- Caching — DVC stores outputs and restores them on re-run, avoiding unnecessary recomputation

**What Roar provided that DVC did not:**
- Zero-configuration pipeline inference — no YAML to write; lineage emerges from actual execution
- Complete file I/O tracing — see exactly which files were read/written, not just declared
- Global artifact discoverability — `roar register` publishes artifacts to GLaaS so external stakeholders can trace lineage without accessing your Git repo

---

#### **Q2 — The DAGs**

*Look at both DAG outputs side by side. Do they show the same pipeline structure? Are there any differences in what each tool captured? Which was easier to understand?*

**Answer:**

**Same structure, different presentation:**
- Both showed: `preprocess → train → evaluate` (three stages, two dependencies)
- DVC DAG: Declarative, shows what you wrote in `dvc.yaml` — stage names and dependencies are explicit
- Roar DAG: Observational, shows actual file I/O — captures which files flowed between jobs

**Differences:**
- DVC DAG is cleaner and more abstract (focused on pipeline logic)
- Roar DAG can show finer-grained dependencies if files have multiple readers/writers
- If you had modified a script without changing behavior, DVC would still list it as a dependency; Roar would too (because the file was accessed)

**Easier to understand:**
- **DVC DAG was easier** — human-written, explicit stage names, clear purpose
- **Roar DAG required more interpretation** — you had to correlate file hashes back to job numbers to understand the flow

---

#### **Q3 — Handling changes**

*When you changed a hyperparameter (DVC) or augmented the dataset (Roar), how did each tool respond? With DVC, what determined which stages re-ran? With Roar, who decided what to re-run?*

**Answer:**

**DVC's response to hyperparameter change:**
1. Edited `params.yaml` (e.g., `n_estimators: 50 → 100`)
2. Ran `dvc repro` — DVC detected that `train` stage's param dependency changed
3. Skipped `preprocess` (its dependencies hadn't changed), re-ran `train` and `evaluate`
4. **Decision logic**: DVC compared file hashes in `dvc.lock` to current files. If a Stage's dependency hash changed, DVC re-ran it and all downstream stages.

**Roar's response to dataset augmentation:**
1. Ran `python3 scripts/augment_data.py` (modified `data/raw/data.csv`)
2. Ran `roar run python3 scripts/preprocess.py` — Roar executed it (it always executes what you tell it)
3. Ran `roar run python3 scripts/train.py` and `roar run python3 scripts/evaluate.py`
4. **Decision logic**: User decides what to re-run. Roar doesn't auto-skip; it just logs what you execute.

**Key difference:**
- **DVC**: Automatic, smart — only re-runs what's necessary
- **Roar**: Manual, explicit — you control what runs; Roar is a faithful recorder, not an optimizer

---

#### **Q4 — Experiment tracking and comparison**

*You ran multiple experiments with both DVC and Roar. How did you find and compare results across runs in each tool? How can you trace back which data version and which parameters produced a specific model? Which tool made this easier?*

**Answer:**

**DVC experiment comparison:**
- Ran 3 experiments: `dvc exp run -S train.n_estimators=150 -S train.max_depth=20`, etc.
- Compared with: `dvc exp show` — displayed all experiments in a single table with parameters and metrics side-by-side
- **Result**: Instant visual comparison; could immediately see that Experiment 1 had highest F1-score
- **Tracing back**: `dvc exp apply <exp-name>` restored `params.yaml` and `dvc.lock` to that run; `git log` showed the Git commit; `dvc repro` could re-execute to verify reproducibility

**Roar experiment comparison:**
- Ran 3 experiments: edited `params.yaml`, committed, then `roar run python3 scripts/train.py` and `roar run python3 scripts/evaluate.py`
- Compared with: `roar show @2`, `roar show @4`, `roar show @6` (manually inspecting each job)
- **Result**: Cumbersome; had to manually extract metrics from each job output and correlate to Git commits
- **Tracing back**: `roar show @N` displayed exact command and Git commit; cross-referencing commits to parameters required manual work

**Which was easier:**
- **DVC was significantly easier** — `dvc exp show` is designed exactly for this purpose
- **Roar required manual effort** — suited for tracing lineage, not for automated comparison

---

#### **Q5 — Team collaboration**

*Imagine a new teammate joins your project next month. With DVC, they can read `dvc.yaml` in the Git repo. With Roar, they can look up artifact lineage on GLaaS. Which gives a clearer picture of the pipeline? Could you use both tools together — and if so, how?*

**Answer:**

**DVC for internal collaboration:**
- New teammate clones repo, reads `dvc.yaml` — pipeline structure is immediately clear
- Runs `dvc pull` to fetch data without re-downloading from original source
- Can run `dvc repro` to verify reproducibility or `dvc exp run` to test new ideas
- **Clear for teammates because**: Human-readable YAML, explicit dependencies, standard Git workflow

**Roar for external stakeholders:**
- External collaborator (or auditor) searches artifact hash on GLaaS
- Sees the complete lineage: which data, which code version, which parameters produced the model
- Does NOT need Git repo access or to understand your setup
- **Clear for stakeholders because**: Content hash is globally unique; lineage is self-contained; can share model without sharing entire project

**Using both together:**
- **Best practice**: Use DVC for internal pipeline management + experiment tracking
- **Also use Roar**: Register final models and datasets to GLaaS for external visibility
- **Workflow**: DVC for "how do we build and iterate on this pipeline internally?" + Roar for "let external stakeholders trace this artifact back to its origins"
- **Example**: After `dvc exp apply <best-exp>`, run `roar register models/classifier.pkl` to publish lineage globally
- **Result**: Team has full reproducibility (DVC); external stakeholders have artifact traceability (Roar)

---

#### **Q6 — Your project**

*For your team's course project, which approach (or combination) would be more useful? Consider your data sources, pipeline complexity, and how your team collaborates.*

**Answer:**

**Recommended approach for course project: DVC + Roar**

- **Use DVC as primary tool** because:
  - Course projects typically involve small datasets and simple pipelines (well-suited to DVC's declarative model)
  - Team collaboration happens via shared Git repo (the standard in coursework)
  - `dvc exp run` enables rapid parameter exploration (useful for quick iteration)
  - `dvc repro` ensures reproducibility for project checkpoints (useful for demo/grading)

- **Use Roar for final submission** because:
  - `roar register` creates a permanent, globally-identifiable record of your final model
  - Graders/TAs can trace lineage via GLaaS without cloning your repo
  - Demonstrates understanding of implicit lineage tracking (part of the learning objective)
  - Adds polish to final deliverable

- **Workflow for course project**:
  1. Use `dvc.yaml` throughout project development (team collaboration, experiment tracking)
  2. Run pipeline with `dvc repro` for checkpoints
  3. Final submission: register best model with `roar register` + provide GLaaS URL to graders
  4. Include both `dvc dag` and `roar dag` outputs in writeup

---

In this lab you will run the same ML pipeline through two tools that take fundamentally different approaches to pipeline tracking and reproducibility:

- **DVC (Data Version Control)** — a *declarative* tool where you explicitly define your pipeline stages, dependencies, and outputs in a YAML file. You tell DVC what your pipeline looks like.
- **Roar (Run Observation & Artifact Registration)** — an *implicit* tool that observes file I/O as your code runs and automatically infers the dependency graph. You just run your code; Roar figures out the pipeline.

By using both on the same pipeline, you will understand not just how each tool works, but *why* these different design philosophies exist and when each is appropriate.


## Learning Objectives

1. Version datasets and models using DVC alongside Git
2. Run declarative, reproducible ML pipelines with `dvc.yaml`
3. Run and compare experiments with DVC's experiment tracking
4. Use Roar to implicitly track pipeline lineage without configuration files
5. Inspect and interpret auto-inferred lineage DAGs
6. Articulate when to use declarative (DVC) vs. observational (Roar) pipeline tracking

## The Dataset and Model

This lab uses the **Breast Cancer Wisconsin (Diagnostic)** dataset (569 samples, 30 numeric features computed from digitized images of breast tissue). The target variable is binary: **malignant (0)** or **benign (1)**. The pipeline trains a **Random Forest classifier** to predict the diagnosis from the features.

The dataset is small enough to version in Git for convenience, but in a real project this is exactly the kind of artifact you would manage with DVC.

## Deliverables

- **Deliverable 1 (Run DVC & Roar)**: Complete the step-by-step instructions in [INSTRUCTIONS.md](INSTRUCTIONS.md). Show the TA:
  - Your `dvc dag` output and `roar dag` output
  - The registered artifact lineage on [glaas.ai](https://glaas.ai/)

- **Deliverable 2 (Experimentation)**: Run 2–3 experiments with parameters you choose (different from the defaults in `params.yaml`) using **both** DVC and Roar. Show the TA how you compare results across runs in each tool and how you can trace back which data and parameters produced a given model.

- **Deliverable 3 (Reflection)**: Complete the [summary table](#summary-table) below and be prepared to discuss the [reflection questions](#reflection-questions) with the TA.

## How to Use This Repo

| File | What it contains |
|------|-----------------|
| **This README** | Overview, setup, reflection questions, and deliverables |
| [**INSTRUCTIONS.md**](INSTRUCTIONS.md) | Step-by-step commands for DVC (Part 1) and Roar (Part 2) |
| [**TROUBLESHOOTING.md**](TROUBLESHOOTING.md) | Common errors and how to fix them |

---

## Setup

### Prerequisites

- Git installed
- Python 3.10+ (installed via Homebrew, pyenv, or a standard installer — **not** the macOS system Python at `/usr/bin/python3`)
- A terminal environment (see platform notes below)

> **Platform notes**:
> - **macOS**: Both DVC and Roar work natively. Roar requires a non-Apple Python (Homebrew, pyenv, conda, or python.org installer). Run `which python3` — if it shows `/usr/bin/python3`, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md). If you run into any issues on macOS, we recommend that you work on your team's VM.
> - **Windows**: DVC works natively. Roar requires **WSL2** (Windows Subsystem for Linux). Install it with `wsl --install` in PowerShell if you don't have it, then do the entire lab inside WSL. If you run into any issues on Windows, we recommend that you work on your team's VM.
> - **Linux**: Everything works out of the box.

### Installation

1. Clone this repository:

```bash
git clone https://github.com/AshrithaG/mlip-lab-9.git
cd mlip-lab-9
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Verify Roar installed correctly:

```bash
roar --version
```

### Repository Structure

```
mlip-lab-9/
├── data/raw/data.csv          # Breast Cancer Wisconsin dataset (569 samples, 30 features)
├── scripts/
│   ├── preprocess.py          # Train/test split
│   ├── train.py               # Random Forest training
│   ├── evaluate.py            # Model evaluation (accuracy, precision, recall, F1)
│   └── augment_data.py        # Adds synthetic rows to the dataset
├── params.yaml                # Hyperparameters for the pipeline
├── dvc.yaml                   # DVC pipeline definition (3 stages)
└── requirements.txt
```

### Verify the Pipeline

Before using any versioning tools, make sure the pipeline runs end-to-end:

```bash
python3 scripts/preprocess.py
python3 scripts/train.py
python3 scripts/evaluate.py
```

You should see output showing the data split, trained model parameters, and evaluation metrics. Fix any errors before proceeding.

---

**Next step**: Open [INSTRUCTIONS.md](INSTRUCTIONS.md) to begin Part 1 (DVC) and Part 2 (Roar). Once you have completed both parts, return here for Part 3.

---

## Part 3: Compare and Reflect

You have now used both tools on the same pipeline. Fill in the summary table and be ready to discuss the questions below with the TA. Refer to the official documentation as needed:

- [DVC Pipelines Guide](https://dvc.org/doc/user-guide/pipelines)
- [DVC Experiments Guide](https://dvc.org/doc/user-guide/experiment-management)
- [Roar on PyPI](https://pypi.org/project/roar-cli/)
- [GLaaS — Global Lineage as a Service](https://glaas.ai/)

### Reflection Questions

**Q1 — Setup and configuration**:
Compare the setup effort for DVC vs. Roar. What did you have to configure explicitly for DVC that Roar handled automatically? What did DVC give you that Roar did not?

**Q2 — The DAGs**:
Look at both DAG outputs side by side. Do they show the same pipeline structure? Are there any differences in what each tool captured? Which was easier to understand?

**Q3 — Handling changes**:
When you changed a hyperparameter (DVC) or augmented the dataset (Roar), how did each tool respond? With DVC, what determined which stages re-ran? With Roar, who decided what to re-run?

**Q4 — Experiment tracking and comparison**:
You ran multiple experiments with both DVC and Roar. How did you find and compare results across runs in each tool? How can you trace back which data version and which parameters produced a specific model? Which tool made this easier?

**Q5 — Team collaboration**:
Imagine a new teammate joins your project next month. With DVC, they can read `dvc.yaml` in the Git repo. With Roar, they can look up artifact lineage on GLaaS. Which gives a clearer picture of the pipeline? Could you use both tools together — and if so, how?

**Q6 — Your project**:
For your team's course project, which approach (or combination) would be more useful? Consider your data sources, pipeline complexity, and how your team collaborates.

### Summary Table

Fill in the following table based on your experience (replace the blanks):

| | DVC | Roar |
|---|---|---|
| **Philosophy** | ____________ | ____________ |
| **Config required** | ____________ | ____________ |
| **How is the DAG defined?** | ____________ | ____________ |
| **What happens on re-run?** | ____________ | ____________ |
| **How are artifacts versioned?** | ____________ | ____________ |
| **Reproducibility mechanism** | ____________ | ____________ |
| **Collaboration model** | ____________ | ____________ |
| **Platform support** | ____________ | ____________ |


## Resources

- [DVC Documentation](https://dvc.org/doc)
- [DVC Pipelines Guide](https://dvc.org/doc/user-guide/pipelines)
- [DVC Experiments Guide](https://dvc.org/doc/user-guide/experiment-management)
- [Roar on PyPI](https://pypi.org/project/roar-cli/)
- [GLaaS — Global Lineage as a Service](https://glaas.ai/)
