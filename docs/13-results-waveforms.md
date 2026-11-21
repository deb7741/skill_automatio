# 13 · Results and waveforms

## 1. Formats at a glance

| Format | Produced by | Viewer | Scriptable access |
|---|---|---|---|
| **PSF binary** (`psfbin`) | Spectre (classic default) | ViVA | Ocean, `libpsf`, `psf` converter |
| **PSF-XL** (`psfxl`) | Spectre/APS/X (default from ADE in newer setups) | ViVA | Ocean; export to CSV/ASCII |
| **PSF ASCII** (`psfascii`) | Spectre `-format psfascii` | ViVA, text editor | `psf_utils`, `vautil.psf_ascii` |
| **nutascii / nutbin** | Spectre `-format nutascii` | Many SPICE viewers | Simple text parsers |
| **SST2** (`.trn/.dsn`) | Spectre, AMS | SimVision, ViVA | Tcl, conversion tools |
| **SHM** (`.shm/`) | Xcelium, AMS digital side | SimVision | Tcl (`simvision`), conversions |
| **UDB** | Spectre FX (default) | ViVA | Ocean / conversion |
| **FSDB** | Spectre FX / third-party PLI | Verdi | Third-party tools |
| **VCD** | Any Verilog sim | Everything | Open-source parsers |

Spectre's `-format` option picks the output. For scripted Python post-processing, **`psfascii`** is the easiest. It's larger and slower to write, so use it for automation runs, not giant transients.

## 2. Inside a PSF results directory

```text
psf/
├── logFile             # list of analyses that ran (used by ViVA/Ocean)
├── tran1.tran          # transient results (name = analysis instance name + type)
├── ac1.ac
├── dcop.dc / dcOp.dc   # operating point
├── element.info, modelParameter.info, ...   # device info
└── runObjFile          # PSF-XL / ADE bookkeeping
```

Sweep and Monte Carlo runs create files like `swp1-000_t1.tran`, `mc1-001_a1.ac` (one per point).

## 3. ViVA (Virtuoso Visualization & Analysis)

- Open results from the CIW: **Tools → Analog Environment → Results Browser**, or `openResults("psf")` then `plot(v("/out"))` in Ocean.
- **Calculator** expressions (e.g. `bandwidth(VF("/out") 3 "low")`) are the same functions Ocean uses. Build an expression in the GUI, then copy it into your script.
- Export: right-click a trace → **Send To → Export** (CSV), or `ocnPrint` from Ocean.

## 4. SimVision

- `simvision waves.shm` (Xcelium) or open the AMS run's databases.
- Save a signal layout with **File → Save Command Script** (`.svcf`) and reload it with `simvision -input view.svcf`. Commit these for your testbenches.
- Analog traces in AMS runs can be shown as analog waveforms (right-click → *Format → Analog*).

## 5. Conversions

| From → To | Command |
|---|---|
| PSF (any) → PSF ASCII | `psf -i tran1.tran -o tran1.psfascii` (Cadence `psf` utility) |
| Waveform → CSV | Ocean `ocnPrint(?output "x.csv" ...)`, ViVA export |
| SHM → VCD | `simvisdbutil waves.shm -vcd -output waves.vcd` (check `simvisdbutil -help`) |

## 6. Keep results small

- Save only what you measure: `save out in` or `save=selected` in Spectre; selective Tcl probes in Xcelium.
- Use `strobeperiod`/`outputstart` in `tran` (or ADE's "output start") to skip uninteresting time.
- Delete PSF directories after extracting metrics in regressions. Keep CSV summaries and logs.

Next: [14 · Troubleshooting](14-troubleshooting.md)
