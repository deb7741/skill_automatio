# 01 · Environment setup

A clean, reproducible environment is the foundation of every automation flow. Most "my script works for me but not for you" problems come from a different `cds.lib`, `.cdsinit` or `PATH`.

## 1. Release families (what you probably have installed)

| Family | Example install name | Main executables | Notes |
|---|---|---|---|
| Virtuoso IC | `IC618` (IC6.1.8 ISRxx), `ICADVM201`, `IC231`, `IC251` | `virtuoso`, `ocean`, `si`, `cdsLibMgr` | IC6.1.8 = this guide's baseline. IC23.1/IC25.1 are branded "Virtuoso Studio" |
| Spectre (formerly MMSIM) | `SPECTRE181`, `SPECTRE211`, `SPECTRE231`, ... | `spectre`, `aps`, `spectrefx`, `psf` | Spectre APS/X/FX are modes or binaries of the same product |
| Xcelium (formerly Incisive) | `XCELIUM1809`, `XCELIUM2309`, ... | `xrun`, `xmvlog`, `xmelab`, `xmsim`, `simvision`, `imc` | `irun` → `xrun`, `nc*` → `xm*` |
| Verisium / Indago, vManager | varies | `verisium`, `vmanager` | Optional debug and regression management tools |

Check what is on your `PATH`:

```bash
virtuoso -W          # Virtuoso version
spectre -W           # Spectre version (short)
spectre -V           # Spectre version (long)
xrun -version        # Xcelium version
which virtuoso spectre xrun ocean si
```

Virtuoso, Spectre and Xcelium are released separately. Each Virtuoso README lists the Spectre/Xcelium versions it was qualified with, so check it before you mix releases.

## 2. Shell environment

Full templates: [`scripts/setup_env.sh.template`](../scripts/setup_env.sh.template) (bash) and [`scripts/setup_env.csh.template`](../scripts/setup_env.csh.template) (tcsh). The essentials:

```bash
# --- install roots (placeholders) ---
export CDSHOME=/path/to/cadence/IC618          # Virtuoso
export SPECTRE_HOME=/path/to/cadence/SPECTRE211
export XCELIUM_HOME=/path/to/cadence/XCELIUM2309

# --- PATH: order matters if several releases are installed ---
export PATH=$CDSHOME/tools/bin:$CDSHOME/tools/dfII/bin:$PATH
export PATH=$SPECTRE_HOME/bin:$PATH
export PATH=$XCELIUM_HOME/tools/bin:$PATH

# --- licenses ---
export CDS_LIC_FILE=5280@<license-server>      # or LM_LICENSE_FILE

# --- commonly used Cadence variables ---
export CDS_Netlisting_Mode=Analog              # analog netlisting mode for ADE
export CDS_LOAD_ENV=CWDElseHome                # load .cdsenv from CWD, else $HOME
```

Tips:

- **Use a project setup script**, not personal `.bashrc` edits, so every user and every CI job gets the same tools.
- If your site uses *modules* (`module load cadence/IC618`), call that from the setup script.
- Don't hard-code license servers in scripts you share. Read them from the environment.

## 3. The Virtuoso startup files

| File | Purpose | Where it is searched |
|---|---|---|
| `cds.lib` | Defines libraries (name → directory) | Current directory first, then per `setup.loc` |
| `.cdsinit` | SKILL executed at startup (bindkeys, loading utilities, env settings) | Site `$CDSHOME/tools/dfII/local/.cdsinit` if present, then CWD or `$HOME` (site setups vary) |
| `.cdsenv` | Default values for tool options (`envSetVal`-style settings) | Controlled by `CDS_LOAD_ENV` |
| `.simrc` | Simulation environment defaults (ADE/Ocean) | CWD / `$HOME` |
| `setup.loc` | Search order for Cadence Search File mechanism (CSF) | `$CDSHOME/share/cdssetup/setup.loc` + local override |
| `display.drf` | Display resources (layer colors). Usually from PDK, so **not** covered here | |
| `si.env` | Netlisting settings for `si` (batch netlister) | Run directory |

### 3.1 `cds.lib`

```text
-- comments start with two dashes
SOFTINCLUDE $CDSHOME/share/cdssetup/cdsDefTechLib/cds.lib   -- optional, site-specific
DEFINE analogLib $CDSHOME/tools/dfII/etc/cdslib/artist/analogLib
DEFINE basic     $CDSHOME/tools/dfII/etc/cdslib/basic
DEFINE ahdlLib   $CDSHOME/tools/dfII/samples/artist/ahdlLib
DEFINE myLib     ./libs/myLib
INCLUDE /path/to/project/cds.lib.project                     -- PDK & shared libs live here
```

- `DEFINE` adds a library, `UNDEFINE` removes one, `INCLUDE` pulls in another file (error if missing), `SOFTINCLUDE` is the same but silent if missing.
- Use **environment variables** in paths so the file moves between sites.
- Check what got loaded with `ddGetLibList()~>name` in the CIW.
- Template: [`templates/cds.lib.template`](../templates/cds.lib.template).

> The exact location of `analogLib`/`basic` inside the install tree is stable across IC6.1.x and IC23.1, but verify with `find $CDSHOME/tools/dfII/etc/cdslib -maxdepth 2 -name cdsinfo.tag`.

### 3.2 `.cdsinit`

Keep it short. Load a project file rather than pasting everything in:

```lisp
; .cdsinit
printf("Loading project .cdsinit\n")
let((projInit)
  projInit = getShellEnvVar("PROJ_SKILL_INIT")
  when(projInit && isFile(projInit)
    loadi(projInit)))           ; loadi = keep going on error

; personal settings last, so they override project defaults
when(isFile("~/.cdsinit.personal") loadi("~/.cdsinit.personal"))
```

Template with common, safe settings: [`templates/cdsinit.template`](../templates/cdsinit.template).

### 3.3 `.cdsenv`

Format: `tool[.partition]  variable  type  value`

```text
asimenv.startup   projectDir  string  "./simulation"
spectre.envOpts   controlMode string  "batch"
```

Find a variable's exact name: set it in the GUI, then run `envGetVal("asimenv.startup" "projectDir")` in the CIW. Or open **CIW → Options → Save Defaults** and look at the generated file.

## 4. Licenses

```bash
lmstat -a -c $CDS_LIC_FILE | less               # what's available / in use
lmstat -f Virtuoso_Schematic_Editor_L -c $CDS_LIC_FILE
```

- Batch tools wait or fail when licenses are busy. Spectre has `+lqtimeout <sec>` (license queue timeout). Xcelium has `-licqueue`.
- In regressions, **throttle parallel jobs to the license count**, not the CPU count.

## 5. Directory layout that scales

```text
project/
├── cds.lib                 # includes shared + personal libs
├── .cdsinit -> setup/cdsinit
├── setup/                  # env scripts, cdsinit, cdsenv
├── libs/                   # your design libraries (under DM: git/SOS/DesignSync/ClioSoft)
├── models/                 # Verilog-A / RNM models (no PDK content in public repos!)
├── sim/                    # simulation run dirs (never commit)
├── scripts/                # SKILL / Ocean / Python / shell
└── regress/                # test lists, results, reports
```

## 6. Sanity checklist

```bash
$ source setup_env.sh
$ virtuoso -W && spectre -W && xrun -version
$ cd project && virtuoso -nograph -restore /dev/null -log /tmp/v.log; tail /tmp/v.log
```

In the CIW:

```lisp
getVersion()                ; Virtuoso version string
getShellEnvVar("CDSHOME")
ddGetLibList()~>name        ; libraries defined
envGetVal("asimenv.startup" "projectDir")
```

Next: [02 · Tool landscape](02-tool-landscape.md)
