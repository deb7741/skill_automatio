# Documentation index

| # | Chapter | You will learn |
|---|---|---|
| 01 | [Environment setup](01-environment-setup.md) | Env vars, `cds.lib`, `.cdsinit`, `.cdsenv`, licenses, version checks |
| 02 | [Tool landscape](02-tool-landscape.md) | What every tool is for, and which automation entry point to pick |
| 03 | [Spectre from the command line](03-spectre-command-line.md) | Netlist syntax, analyses, sweeps, Monte Carlo, APS/X/FX, output formats |
| 04 | [Ocean scripting](04-ocean-scripting.md) | Batch ADE-style runs, parametric/PVT loops, measurement functions, exporting |
| 05 | [SKILL fundamentals](05-skill-fundamentals.md) | Syntax, lists, control flow, files, strings, debugging, SKILL++ |
| 06 | [SKILL for design automation](06-skill-design-automation.md) | Database access, schematic generation, CDF, netlisting, batch Virtuoso |
| 07 | [ADE Explorer/Assembler automation](07-ade-assembler-automation.md) | `mae*` API, batch maestro runs, exporting results, Ocean XL |
| 08 | [Xcelium and `xrun`](08-xcelium-xrun.md) | Compile/elab/sim, SV/UVM, Tcl probes, waves, coverage |
| 09 | [Spectre AMS Designer](09-ams-designer.md) | `amsd` blocks, IE cards, connect rules, AMS with `xrun`, debugging |
| 10 | [Behavioral modeling](10-behavioral-modeling.md) | Verilog-A, Verilog-AMS, wreal, SystemVerilog RNM, model validation |
| 11 | [Python integration](11-python-integration.md) | skillbridge, subprocess drivers, PSF reading, reports |
| 12 | [Regression, batch and CI](12-regression-ci-batch.md) | Batch modes, LSF/SGE, exit codes, JUnit XML, Jenkins/GitLab |
| 13 | [Results and waveforms](13-results-waveforms.md) | PSF/PSF-XL/SST2/SHM/FSDB/UDB, ViVA, SimVision, conversion |
| 14 | [Troubleshooting](14-troubleshooting.md) | Licenses, libraries, netlisting, convergence, AMS, xrun errors |
| 15 | [Cheat sheets](15-cheatsheets.md) | One-page command and function references |
| — | [Glossary](glossary.md) | Acronyms and jargon |
| — | [References](references.md) | Where to find official docs and good community material |

## Conventions used in these docs

- `$ command`: shell (bash unless noted)
- `> expression`: CIW / Ocean / SKILL prompt
- `/path/to/...`, `myLib`, `myCell`, `<server>`: placeholders you replace
- **IC6.1.8**: base release this guide targets. Notes marked **IC23.1+** describe newer behavior
- Function signatures are simplified to the arguments you use most. Run `help('functionName)` in the CIW, use the SKILL API Finder, or check `cdnshelp` for full signatures
