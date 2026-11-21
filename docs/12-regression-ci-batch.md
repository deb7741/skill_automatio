# 12 · Regression, batch and CI

## 1. Batch entry points (summary)

| Tool | Batch command | Pass/fail signal |
|---|---|---|
| Spectre | `spectre in.scs =log run.log -raw psf` | Exit code + log (`ERROR`, convergence) |
| Ocean | `ocean -nograph -restore s.ocn` | Your own marker line in stdout, CSV contents |
| Virtuoso SKILL | `virtuoso -nograph -restore s.il -log s.log` | Marker line (`BATCH_STATUS: PASS`) |
| Assembler | `virtuoso -nograph -restore run_maestro.il` | Exported CSV vs specs |
| Xcelium | `xrun -f files.f -l x.log` | Exit code + log (`*E`, `UVM_ERROR`, banner) |
| AMS | `xrun ... amscf.scs` | Same as Xcelium + analog log |

**Rule:** never trust exit codes alone. Every job should produce a **machine-readable verdict** (marker line, JSON, CSV, JUnit XML).

## 2. A regression layout that works

```text
regress/
├── tests.yaml           # list of tests: name, tool, inputs, timeout, tags
├── run_regression.py    # orchestrator (reads tests.yaml, runs in parallel)
├── specs/               # JSON specs per testbench
└── out/<date>/<test>/   # one directory per test run: logs, psf, csv, verdict.json
```

[`examples/python/xrun_regression.py`](../examples/python/xrun_regression.py) and [`spectre_sweep.py`](../examples/python/spectre_sweep.py) show the core patterns: per-test directories, parallel workers, timeouts, log parsing, JUnit output.

## 3. Compute farms (LSF / SGE / Slurm)

Wrap the tool command in the scheduler submit command:

```bash
# LSF
bsub -q normal -n 4 -R "rusage[mem=8000]" -o lsf_%J.log -K \
     spectre in.scs +mt=4 =log run.log -raw psf
# SGE
qsub -b y -cwd -pe smp 4 -o sge.log -sync y spectre in.scs +mt=4 =log run.log
# Slurm
srun -c 4 --mem=8G spectre in.scs +mt=4 =log run.log
```

- `-K` (LSF) / `-sync y` (SGE) block until the job finishes, which keeps the orchestrator simple.
- Request the same thread count you pass to the simulator (`+mt=N`).
- ADE Assembler submits to farms itself through **Job Setup**. Don't double-wrap.
- Template: [`scripts/submit_lsf.sh`](../scripts/submit_lsf.sh).

## 4. Licenses are the real bottleneck

- Limit concurrency to available licenses: `lmstat -f <feature>` before launching, or a semaphore in your orchestrator.
- Use queueing options (`+lqtimeout`, `-licqueue`) so jobs wait instead of failing, but with a timeout so CI doesn't hang forever.
- Schedule heavy regressions at night. Keep a small "smoke" set for every commit.

## 5. CI servers (Jenkins / GitLab CI / GitHub Actions self-hosted)

Cadence tools must run on **your own licensed machines**. Use self-hosted runners/agents inside your network. **Never attach a self-hosted runner to a public repository**: anyone could open a pull request that runs code on your machine. Keep the repository that holds your real regression private. Public cloud CI can only run the tool-independent parts (Python unit tests, lint, PDK-term checks), which is exactly what this repo's own `.github/workflows/ci.yml` does.

GitLab CI sketch (self-hosted runner tagged `cadence`):

```yaml
stages: [smoke, nightly]

smoke:
  stage: smoke
  tags: [cadence]
  script:
    - source setup/setup_env.sh
    - python3 regress/run_regression.py --tags smoke --junit out/junit.xml
  artifacts:
    when: always
    reports: { junit: out/junit.xml }
    paths: [out/]

nightly:
  stage: nightly
  tags: [cadence]
  rules: [{ if: '$CI_PIPELINE_SOURCE == "schedule"' }]
  script:
    - source setup/setup_env.sh
    - python3 regress/run_regression.py --all --jobs 16 --junit out/junit.xml
  artifacts: { when: always, reports: { junit: out/junit.xml } }
```

Jenkins: same commands in a `sh` step, with `junit 'out/junit.xml'` in `post { always { ... } }`.

## 6. Making runs reproducible

- **Pin tool versions** in the setup script (no "latest" symlinks in CI).
- **Pin seeds** (`-svseed`, Monte Carlo `seed=`). Log them so failures can be reproduced.
- **Record the environment**: tool versions, git commit, host, and date in every `verdict.json`. Keep these outputs in private storage, never in a public repo; they reveal site details.
- **Clean run dirs** (`xrun -clean`, fresh `-raw` directories), so stale results can't make a broken test pass.
- **Netlist once** per regression, then simulate many times from the same netlist.

## 7. Timeouts and hangs

- Every job needs a wall-clock timeout (`subprocess.run(..., timeout=...)`, scheduler limits).
- Spectre runs can stall on convergence. Combine a timeout with log parsing for "time step too small" and similar messages.
- Virtuoso batch jobs can hang waiting on dialogs. Use `-nograph`, avoid GUI functions in batch code, and set the env options that disable confirmation prompts where possible.

## 8. Reporting

- JUnit XML for the CI dashboard
- A Markdown/HTML summary per run (spec table, failing tests first, links to logs)
- Trend tracking: append key metrics (bandwidth, offset, runtime) to a CSV per night and plot it. Slow drifts show up long before hard failures.

Next: [13 · Results and waveforms](13-results-waveforms.md)
