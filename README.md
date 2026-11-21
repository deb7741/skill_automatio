# skill_automatio: Virtuoso Automation Guide

This repo can be used by people who want to work faster in Cadence.

**A practical, PDK-free help guide for automating Cadence® Virtuoso® simulation and verification flows: Spectre, Ocean, SKILL, ADE Explorer/Assembler, Xcelium (`xrun`), Spectre AMS Designer and Python.**

> Focus release: **Virtuoso IC6.1.8** (most content also applies to ICADVM18.1/20.1, IC23.1 and IC25.1 "Virtuoso Studio").
> No foundry PDK content: every example uses only Cadence's generic libraries (`analogLib`, `basic`, `ahdlLib`) or plain Verilog-A/SystemVerilog models written for this repo.

---

## Who this is for

- Analog/mixed-signal designers who are tired of clicking through ADE for the 50th corner run
- Verification engineers who need to bring analog blocks into an `xrun` regression
- CAD engineers who want a clear starting point for SKILL, Ocean and Python glue scripts
- Students and new hires who need one place that explains how the tools fit together

## What's inside

| Path | What you get |
|---|---|
| [`docs/`](docs/README.md) | 15 chapters, from environment setup to regression/CI, plus cheat sheets and a glossary |
| [`examples/spectre/`](examples/spectre) | Stand-alone Spectre netlists: transient/AC, sweeps, Monte Carlo, Verilog-A |
| [`examples/ocean/`](examples/ocean) | Ocean scripts: basic run, parametric sweep, PVT loop, measurements to CSV |
| [`examples/skill/`](examples/skill) | SKILL utilities: library browsing, schematic generation, batch netlisting, ADE Assembler (maestro) batch runs |
| [`examples/xrun/`](examples/xrun) | Xcelium SystemVerilog example with filelist, Tcl probe and coverage |
| [`examples/ams/`](examples/ams) | AMS Designer: SystemVerilog testbench driving a Spectre/Verilog-A DAC through an `amsd` control file |
| [`examples/rnm/`](examples/rnm) | Real-number models (SystemVerilog `real`) for fast mixed-signal regressions |
| [`examples/veriloga/`](examples/veriloga) | Reusable Verilog-A building blocks (comparator, DAC, ADC, VCO, sample-and-hold) |
| [`examples/python/`](examples/python) | Python: PSF reader, parallel Spectre sweep runner, log parsers, Ocean/xrun drivers, skillbridge demo, spec checker |
| [`templates/`](templates) | `cds.lib`, `.cdsinit`, `.cdsenv`, `si.env`, filelist and AMS control-file templates |
| [`scripts/`](scripts) | Shell environment templates (bash and csh), batch launchers, cleanup |
| [`tools/check_no_pdk.py`](tools/check_no_pdk.py) | Guard that blocks PDK/foundry content and private data (license servers, IPs, e-mails, home paths, keys) |

## Quick start

```bash
git clone https://github.com/deb7741/skill_automatio.git
cd skill_automatio

# 1. Point the environment template at your own install paths
scripts/install_git_hook.sh                      # block accidental leaks on every commit
cp scripts/setup_env.sh.template setup_env.sh   # or setup_env.csh.template (copy is git-ignored)
$EDITOR setup_env.sh
source setup_env.sh

# 2. Run the simplest example (only needs Spectre)
cd examples/spectre/01_rc_lowpass
./run.sh

# 3. Post-process the result in Python (no Cadence license needed)
cd ../../python
pip install -r requirements.txt
python read_psf.py ../spectre/01_rc_lowpass/psf/ac1.ac --list
```

## Learning path

```
 Environment ─► Spectre CLI ─► Ocean ─► SKILL ─► ADE Assembler automation
     (01)          (03)         (04)   (05,06)            (07)
                     │
                     └──► Verilog-A / RNM (10) ─► xrun (08) ─► AMS Designer (09)
                                                       │
                     Python post-processing (11) ◄─────┘
                                │
                     Regression & CI (12)
```

1. [Environment setup](docs/01-environment-setup.md): `cds.lib`, `.cdsinit`, `.cdsenv`, env vars, licenses
2. [Tool landscape](docs/02-tool-landscape.md): which tool does what, and when to use it
3. [Spectre from the command line](docs/03-spectre-command-line.md)
4. [Ocean scripting](docs/04-ocean-scripting.md)
5. [SKILL fundamentals](docs/05-skill-fundamentals.md)
6. [SKILL for design automation](docs/06-skill-design-automation.md)
7. [ADE Explorer/Assembler automation](docs/07-ade-assembler-automation.md)
8. [Xcelium and `xrun`](docs/08-xcelium-xrun.md)
9. [Spectre AMS Designer](docs/09-ams-designer.md)
10. [Behavioral modeling: Verilog-A, Verilog-AMS, RNM](docs/10-behavioral-modeling.md)
11. [Python integration](docs/11-python-integration.md)
12. [Regression, batch and CI](docs/12-regression-ci-batch.md)
13. [Results and waveforms](docs/13-results-waveforms.md)
14. [Troubleshooting](docs/14-troubleshooting.md)
15. [Cheat sheets](docs/15-cheatsheets.md) · [Glossary](docs/glossary.md) · [References](docs/references.md)

## Ground rules

1. **No PDK, foundry or private data.** No model files, layer maps, device names, rule decks, license servers, host names or personal paths. See [DISCLAIMER.md](DISCLAIMER.md) and [SECURITY.md](SECURITY.md). `tools/check_no_pdk.py` enforces this in CI, and as a pre-commit hook if you run `scripts/install_git_hook.sh`.
2. **No copied Cadence documentation.** We explain things in our own words and point to the official manuals (`cdnshelp`, Cadence Support) for full details.
3. **Everything is a template.** Install paths, library names and license servers are placeholders like `/path/to/cadence/IC618`. Change them for your site.
4. **Check your version.** Options change between releases. When in doubt, run `spectre -h`, `xrun -helpall`, or look in the SKILL API Finder (CIW → Tools → SKILL API Finder).

## Running the tests (no Cadence tools needed)

The Python helpers ship with unit tests that use small fixture files, so CI can run anywhere:

```bash
cd examples/python
pip install -r requirements.txt pytest
pytest -q
python ../../tools/check_no_pdk.py ../..
```

## Contributing

Contributions are very welcome: new recipes, fixes for version differences, better explanations. Read [CONTRIBUTING.md](CONTRIBUTING.md) first; the most important rule is **no PDK/NDA content**.

## License

Code and documentation are released under the [MIT License](LICENSE).

Cadence, Virtuoso, Spectre, Xcelium, and other Cadence product names are trademarks of Cadence Design Systems, Inc. This project is community-maintained and is not affiliated with or endorsed by Cadence.
