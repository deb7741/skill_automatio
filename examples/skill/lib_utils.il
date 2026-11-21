;; =====================================================================
;; lib_utils.il : library browsing & reporting utilities
;; Load:   load("lib_utils.il")
;; Tested: IC6.1.8 (should work unchanged in IC23.1/IC25.1)
;; Prefix: vag (Virtuoso Automation Guide)
;; =====================================================================

;; ---------------------------------------------------------------------
;; vagListCells(libName) => sorted list of cell names | nil
;; ---------------------------------------------------------------------
procedure(vagListCells(libName "t")
  let((lib)
    lib = ddGetObj(libName)
    if(lib
      then sort(lib~>cells~>name 'alphalessp)
      else warn("vagListCells: library %s not defined (check cds.lib)\n" libName)
           nil)))

;; ---------------------------------------------------------------------
;; vagCellsWithView(libName viewName) => cells that have viewName
;; e.g. vagCellsWithView("myLib" "maestro")
;; ---------------------------------------------------------------------
procedure(vagCellsWithView(libName viewName "tt")
  let((lib cells)
    lib = ddGetObj(libName)
    when(lib
      cells = setof(c lib~>cells member(viewName c~>views~>name))
      sort(cells~>name 'alphalessp))))

;; ---------------------------------------------------------------------
;; vagReportLibrary(libName csvFile) => number of rows written
;; CSV columns: lib,cell,view,path
;; ---------------------------------------------------------------------
procedure(vagReportLibrary(libName csvFile "tt")
  let((lib port rows)
    lib  = ddGetObj(libName)
    rows = 0
    unless(lib error("vagReportLibrary: library %s not found\n" libName))
    port = outfile(csvFile "w")
    unless(port error("vagReportLibrary: cannot write %s\n" csvFile))
    fprintf(port "lib,cell,view,path\n")
    foreach(cell sort(lib~>cells lambda((a b) alphalessp(a~>name b~>name)))
      foreach(view cell~>views
        fprintf(port "%s,%s,%s,%s\n" libName cell~>name view~>name
                view~>readPath || "")
        rows++))
    close(port)
    printf("vagReportLibrary: wrote %d rows to %s\n" rows csvFile)
    rows))

;; ---------------------------------------------------------------------
;; vagFindInstancesOf(libName masterLib masterCell [viewName])
;;   => list of (cellName count) for every cell in libName whose
;;      viewName (default "schematic") instantiates masterLib/masterCell
;; e.g. vagFindInstancesOf("myLib" "analogLib" "res")
;; ---------------------------------------------------------------------
procedure(vagFindInstancesOf(libName masterLib masterCell
                             @optional (viewName "schematic"))
  let((result cv n)
    foreach(cellName vagCellsWithView(libName viewName)
      cv = dbOpenCellViewByType(libName cellName viewName nil "r")
      when(cv
        n = length(setof(inst cv~>instances
                         inst~>libName == masterLib &&
                         inst~>cellName == masterCell))
        when(n > 0 result = cons(list(cellName n) result))
        dbClose(cv)))
    reverse(result)))

;; ---------------------------------------------------------------------
;; vagPrintLibSummary(libName) : quick human-readable overview
;; ---------------------------------------------------------------------
procedure(vagPrintLibSummary(libName "t")
  let((cells viewCount)
    cells = vagListCells(libName)
    viewCount = makeTable("views" 0)
    foreach(c ddGetObj(libName)~>cells
      foreach(v c~>views viewCount[v~>name] = viewCount[v~>name] + 1))
    printf("Library %s: %d cells\n" libName length(cells))
    foreach(k sort(viewCount~>? 'alphalessp)
      printf("  %-20s %d\n" k viewCount[k]))
    t))

printf("lib_utils.il loaded: vagListCells vagCellsWithView vagReportLibrary vagFindInstancesOf vagPrintLibSummary\n")
