;; =====================================================================
;; create_testbench.il : generate an RC low-pass testbench schematic
;; using only Cadence's generic analogLib (vsource, res, cap, gnd).
;;
;; Connection strategy: a short stub wire + wire label on every terminal.
;; Nets connect by NAME, so placement doesn't need to be exact.
;;
;; Usage (CIW):
;;   load("create_testbench.il")
;;   vagCreateRcTestbench("myLib" "rc_tb")
;; Then open myLib/rc_tb/schematic, launch ADE Explorer, add design
;; variables rval/vdd, analyses, and save a maestro view.
;;
;; Tested: IC6.1.8. CDF parameter names are those of analogLib; a
;; warning is printed (not an error) if a name differs in your release.
;; =====================================================================

;; Absolute coordinates of a terminal's pin on a placed instance
procedure(vagTermPoint(inst termName "dt")
  let((term pinFig)
    term = car(setof(x inst~>master~>terminals x~>name == termName))
    unless(term error("vagTermPoint: %s has no terminal %s\n"
                      inst~>cellName termName))
    pinFig = car(term~>pins)~>fig
    dbTransformPoint(centerBox(pinFig~>bBox) inst~>transform)))

;; Set a CDF parameter value (string), warn if it doesn't exist
procedure(vagSetCdfParam(inst name value "dtt")
  let((cdf param)
    cdf   = cdfGetInstCDF(inst)
    param = cdf && cdfFindParamByName(cdf name)
    if(param
      then param~>value = value t
      else warn("vagSetCdfParam: no CDF param '%s' on %s (%s)\n"
                name inst~>name inst~>cellName)
           nil)))

;; Draw a stub wire away from the instance body and label it with netName
procedure(vagStubLabel(cv inst termName netName @optional (len 0.25))
  let((pt ctr dx dy end wires)
    pt  = vagTermPoint(inst termName)
    ctr = centerBox(inst~>bBox)
    dx  = xCoord(pt) - xCoord(ctr)
    dy  = yCoord(pt) - yCoord(ctr)
    end = if(abs(dx) > abs(dy)
             then (xCoord(pt) + if(dx > 0 len -len)):yCoord(pt)
             else xCoord(pt):(yCoord(pt) + if(dy > 0 len -len)))
    wires = schCreateWire(cv "draw" "full" list(pt end) 0.0625 0.0625 0.0)
    schCreateWireLabel(cv car(wires) end netName "lowerLeft" "R0"
                       "stick" 0.0625 nil)
    car(wires)))

;; Place an instance of lib/cell/symbol
procedure(vagPlace(cv lib cell name origin @optional (orient "R0"))
  let((master)
    master = dbOpenCellViewByType(lib cell "symbol")
    unless(master error("vagPlace: cannot open %s/%s/symbol\n" lib cell))
    schCreateInst(cv master name origin orient)))

;; ---------------------------------------------------------------------
;; vagCreateRcTestbench(libName cellName) => t on success
;; ---------------------------------------------------------------------
procedure(vagCreateRcTestbench(libName cellName "tt")
  let((cv v1 r1 c1 g1 chk)
    unless(ddGetObj(libName)
      error("vagCreateRcTestbench: library %s not defined\n" libName))

    cv = dbOpenCellViewByType(libName cellName "schematic" "schematic" "w")
    unless(cv error("vagCreateRcTestbench: cannot create %s/%s\n" libName cellName))

    ;; --- place ---
    v1 = vagPlace(cv "analogLib" "vsource" "V1" -2.0:0.0)
    r1 = vagPlace(cv "analogLib" "res"     "R1"  0.0:0.0)
    c1 = vagPlace(cv "analogLib" "cap"     "C1"  2.0:0.0)
    g1 = vagPlace(cv "analogLib" "gnd"     "G1"  0.0:-2.0)

    ;; --- connect by labels ---
    vagStubLabel(cv v1 "PLUS"  "in")
    vagStubLabel(cv v1 "MINUS" "gnd!")
    vagStubLabel(cv r1 "PLUS"  "in")
    vagStubLabel(cv r1 "MINUS" "out")
    vagStubLabel(cv c1 "PLUS"  "out")
    vagStubLabel(cv c1 "MINUS" "gnd!")
    ;; the gnd symbol's terminal name can differ between releases: don't fail on it
    unless(errset(vagStubLabel(cv g1 "gnd!" "gnd!") nil)
      warn("could not label gnd symbol terminal; gnd! labels still define ground\n"))

    ;; --- parameters (design variables rval, vdd stay sweepable in ADE) ---
    vagSetCdfParam(r1 "r" "rval")
    vagSetCdfParam(c1 "c" "1n")
    vagSetCdfParam(v1 "srcType" "pulse")
    vagSetCdfParam(v1 "v1"  "0")
    vagSetCdfParam(v1 "v2"  "vdd")
    vagSetCdfParam(v1 "per" "20u")
    vagSetCdfParam(v1 "pw"  "10u")
    vagSetCdfParam(v1 "tr"  "1n")
    vagSetCdfParam(v1 "tf"  "1n")
    vagSetCdfParam(v1 "acm" "1")

    ;; --- check & save ---
    chk = schCheck(cv)            ; => (numErrors numWarnings)
    printf("schCheck %s/%s: %L (errors warnings)\n" libName cellName chk)
    dbSave(cv)
    dbClose(cv)
    car(chk) == 0))

printf("create_testbench.il loaded: vagCreateRcTestbench vagTermPoint vagSetCdfParam vagStubLabel\n")
