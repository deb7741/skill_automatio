# 15 · Cheat sheets

## Spectre

```bash
spectre tb.scs +escchars =log tb.log -raw psf -format psfxl      # basic
spectre tb.scs +aps +mt=4 ...                                   # APS
spectre tb.scs +preset=mx +mt=8 ...                             # Spectre X
spectrefx tb.sp +preset=lx +mt=8                                # Spectre FX (SPICE syntax default)
spectre -h tran | vsource | options | montecarlo                 # built-in docs
spectre -W                                                       # version
psf -i psf/tran1.tran -o tran1.psfascii                          # convert PSF → ASCII
```

```spectre
simulator lang=spectre
global 0
parameters vdd=1 rval=1k
include "models.scs" section=tt        // placeholder, your PDK
ahdl_include "model.va"
V0 (vdd 0) vsource dc=vdd
V1 (in 0)  vsource type=pulse val0=0 val1=vdd period=10n rise=50p fall=50p width=5n
V2 (in 0)  vsource type=pwl wave=[0 0 1n 0 1.1n 1]
V3 (in 0)  vsource type=sine ampl=0.1 freq=1M sinedc=0.5 mag=1
I0 (vdd b) isource dc=10u
save out in V0:p
tran1 tran stop=1u maxstep=1n errpreset=moderate
ac1   ac start=1 stop=1G dec=20
dc1   dc param=vdd start=0 stop=1.2 step=0.01
noise1 noise start=1 stop=1G dec=10 oprobe=V1
swp1  sweep param=temp values=[-40 27 125] { t tran stop=1u }
mc1   montecarlo numruns=100 seed=1 variations=process { a ac start=1 stop=1G dec=10 }
```

## Ocean

```lisp
simulator('spectre)  design("lib" "cell" "schematic")  resultsDir("./sim")
modelFile('("models.scs" "tt"))   analysis('tran ?stop "1u")   analysis('ac ?start 1 ?stop 1G ?dec 20)
desVar("vdd" 1.0)  temp(27)  option('reltol "1e-4")  save('v "/out")
run()   paramAnalysis("vdd" ?values '(0.9 1.0 1.1))  paramRun()
openResults("./sim/psf")  selectResult('tran)  results()  outputs()
v("/out")  i("/V0/PLUS")  value(w 1u)  ymax(w)  ymin(w)  average(w)  rms(w)
cross(w 0.5 1 'rising)  riseTime(w 0 nil 1 nil 10 90)  bandwidth(w 3 "low")
dB20(w)  phase(w)  phaseMargin(lg)  gainMargin(lg)  clip(w 0 1u)  frequency(w)
ocnPrint(?output "x.txt" ?from 0 ?to 1u ?step 1n v("/out"))
exit()
```

## SKILL

```lisp
ddGetLibList()~>name                           ddGetObj("lib")~>cells~>name
cv = dbOpenCellViewByType(lib cell "schematic" nil "r")  ; "a" edit, "w" create
cv~>instances  cv~>nets  cv~>terminals  inst~>master  net~>instTerms
schCreateInst(cv master "I0" 0:0 "R0")   schCheck(cv)  dbSave(cv)  dbClose(cv)
cdfFindParamByName(cdfGetInstCDF(inst) "r")~>value = "1k"
foreach(x lst ...)  foreach(mapcar x lst ...)  setof(x lst cond)  exists(x lst cond)
let((a b) ...)  prog((a) ... return(a))  errset(expr t)
sprintf(nil "%s_%d" s n)  parseString(s ",")  strcat(a b)  pcreMatchp(re s)
p = outfile("f" "w") fprintf(p ...) close(p)   p = infile("f") gets(l p)
system("cmd")  ipcBeginProcess("cmd")  getShellEnvVar("X")
obj~>?  obj~>??  help('fn)  tracef(fn)  sklint(?file "x.il")
```

## ADE Assembler (`mae*`)

```lisp
s = maeOpenSetup("lib" "tb" "maestro" ?mode "a")
maeSetVar("vdd" "1.0" ?session s)
maeSetSetup(?tests '("lib:tb:1") ?enabled t ?session s)
h = maeRunSimulation(?session s)   maeWaitUntilDone('All)
maeExportOutputView(?session s ?historyName h ?fileName "r.csv" ?view "Detail")
maeWriteScript("dump.il" ?session s)
maeCloseSession(?session s ?forceClose t)
```

```bash
virtuoso -nograph -restore run.il -log run.log      # batch
```

## xrun / Xcelium

```bash
xrun -f files.f -top tb -access +r -l xrun.log
xrun -f files.f -gui -access +rwc -linedebug
xrun -f files.f -input probe.tcl                  # Tcl probes/run/exit
xrun -f files.f -elaborate -snapshot snap ; xrun -R -snapshot snap -svseed 7
xrun -uvm -f files.f +UVM_TESTNAME=t1 +UVM_VERBOSITY=UVM_LOW
xrun -f files.f -coverage all -covtest t1 -covoverwrite
imc -execcmd "merge cov_work/scope/* -out m -overwrite"
xrun -clean ; xrun -helpall ; xrun -helpsubject ams
```

```tcl
database -open waves -shm -default
probe -create tb -all -depth all
run 10us
exit
```

## AMS Designer

```bash
xrun -timescale 1ns/1ps tb.sv amscf.scs -access +r -iereport \
     -spectre_args "+aps" -input probe.tcl -l ams.log
```

```spectre
amsd {
    portmap subckt=blk autobus=yes
    config  cell=blk use=spice
    ie vsup=1.8
}
```

```systemverilog
real v; always #10ns v = $cds_get_analog_value("tb.dut.out");
```

## Verilog-A

```verilog
`include "constants.vams"
`include "disciplines.vams"
module m(a, b); inout a, b; electrical a, b;
  parameter real g = 1 from (0:inf);
  analog begin
    @(cross(V(a) - 0.5, +1)) ;
    V(b) <+ transition(V(a) > 0.5 ? 1.0 : 0.0, 0, 1n);
  end
endmodule
```

## Useful environment variables

| Variable | Purpose |
|---|---|
| `CDS_LIC_FILE` / `LM_LICENSE_FILE` | License servers |
| `CDS_Netlisting_Mode=Analog` | Analog netlisting for ADE |
| `CDS_LOAD_ENV` | Where `.cdsenv` is loaded from |
| `CDS_AUTO_64BIT` | 32/64-bit selection (legacy releases) |
| `TMPDIR` | Temp files for simulators (point at fast local disk) |
