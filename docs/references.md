# References

## Official documentation (needs your Cadence installation / account)

| Resource | How to reach it |
|---|---|
| **cdnshelp** | Run `cdnshelp` from a shell with Virtuoso/Spectre/Xcelium on `PATH`. Full manuals for your *installed* versions, the best reference |
| SKILL API Finder | CIW → Tools → SKILL API Finder |
| Built-in tool help | `spectre -h`, `xrun -helpall`, `xrun -helpsubject ams`, `ocnHelp('fn)` |
| Cadence Support (COS) | [support.cadence.com](https://support.cadence.com): app notes, solutions, rapid adoption kits (RAKs), training bytes |
| Release READMEs / What's New | In the install tree and on Cadence Support |

Manuals worth knowing by name (search in `cdnshelp`):

- *Spectre Circuit Simulator Reference* and *User Guide*
- *Spectre X / Spectre FX User Guides*
- *OCEAN Reference*
- *Cadence SKILL Language User Guide* and *SKILL Language Reference*
- *Virtuoso Design Environment SKILL Reference*, *Virtuoso Schematic Editor SKILL Reference*
- *Virtuoso ADE SKILL Reference* (`mae*` functions)
- *Virtuoso ADE Assembler User Guide*, *ADE Explorer User Guide*
- *Xcelium Simulator User Guide*, *xrun User Guide*
- *Spectre AMS Designer and Xcelium Simulator Mixed-Signal User Guide*
- *Cadence Verilog-A Language Reference*, *Verilog-AMS Language Reference*

## Community

- **Cadence Community forums**, especially *Custom IC SKILL*, *Custom IC Design* and *Mixed-Signal Design*. Decades of answered automation questions
- **Cadence blogs** (Analog/Custom Design, Mixed-Signal): release highlights and how-tos

## Open-source tools used or referenced

| Project | Use |
|---|---|
| [skillbridge](https://github.com/unihd-cag/skillbridge) | Python ↔ SKILL bridge |
| [psf_utils](https://pypi.org/project/psf-utils/) | Read PSF ASCII files in Python |
| libpsf | Read binary PSF in Python/C++ |

## Standards

- IEEE 1800 (SystemVerilog), incl. user-defined nettypes for RNM
- Accellera Verilog-AMS Language Reference Manual (Verilog-A is a subset)
- IEEE 1801 (UPF), for low-power mixed-signal verification

## Books (general background)

- Kundert & Zinke, *The Designer's Guide to Verilog-AMS*
- Kundert, *The Designer's Guide to SPICE and Spectre*
