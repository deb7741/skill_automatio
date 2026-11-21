;; =====================================================================
;; design_checks.il : hierarchy walking and simple schematic checks
;; Load: load("design_checks.il")
;; Tested: IC6.1.8
;; =====================================================================

;; Libraries we never descend into (generic Cadence primitives)
vagStopLibs = '("analogLib" "basic" "ahdlLib" "functional" "US_8ths")

;; ---------------------------------------------------------------------
;; vagWalkHierarchy(lib cell [view]) => list of unique "lib/cell" masters
;; used below lib/cell (depth-first). Descends into a master if it has
;; the same view and its library is not in vagStopLibs.
;; ---------------------------------------------------------------------
procedure(vagWalkHierarchy(lib cell @optional (view "schematic") (seen nil))
  let((cv key)
    unless(seen seen = makeTable("vagSeen" nil))
    cv = dbOpenCellViewByType(lib cell view nil "r")
    when(cv
      foreach(master cv~>instHeaders
        key = strcat(master~>libName "/" master~>cellName)
        unless(seen[key]
          seen[key] = t
          unless(member(master~>libName vagStopLibs)
            when(ddGetObj(master~>libName master~>cellName view)
              vagWalkHierarchy(master~>libName master~>cellName view seen)))))
      dbClose(cv))
    sort(seen~>? 'alphalessp)))

;; ---------------------------------------------------------------------
;; vagFindFloatingNets(cv) => names of nets with fewer than 2 connections
;; (instance terminals + a pin counts as one connection)
;; ---------------------------------------------------------------------
procedure(vagFindFloatingNets(cv "d")
  let((nconn)
    setof(net cv~>nets
      progn(
        nconn = length(net~>instTerms) + if(net~>term 1 0)
        nconn < 2))~>name))

;; ---------------------------------------------------------------------
;; vagCheckAllSchematics(libName ?save nil) => list of (cell errors warnings floating)
;; With ?save t, schematics are opened for edit, checked and saved
;; (only if schCheck reports no errors). Without it: read-only report.
;; ---------------------------------------------------------------------
procedure(vagCheckAllSchematics(libName @key (save nil))
  let((report cv chk floating mode)
    mode = if(save "a" "r")
    foreach(cellName setof(c ddGetObj(libName)~>cells
                           member("schematic" c~>views~>name))~>name
      cv = dbOpenCellViewByType(libName cellName "schematic" nil mode)
      if(cv then
        chk = if(save schCheck(cv) list(0 0))
        floating = vagFindFloatingNets(cv)
        when(save && car(chk) == 0 && dbIsCellViewModified(cv) dbSave(cv))
        report = cons(list(cellName car(chk) cadr(chk) floating) report)
        dbClose(cv)
      else
        report = cons(list(cellName "OPEN_FAILED" nil nil) report)))
    report = reverse(report)
    printf("%-30s err warn  floating-nets\n" "cell")
    foreach(r report
      printf("%-30s %L %L  %L\n" car(r) cadr(r) caddr(r) nth(3 r)))
    report))

printf("design_checks.il loaded: vagWalkHierarchy vagFindFloatingNets vagCheckAllSchematics\n")
