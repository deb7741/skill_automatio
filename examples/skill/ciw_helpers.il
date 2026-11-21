;; =====================================================================
;; ciw_helpers.il : small interactive conveniences (load from .cdsinit)
;; Tested: IC6.1.8
;; =====================================================================

;; Print information about the selected instances in the current window
procedure(vagPrintSelected()
  let((sel)
    sel = geGetSelSet()
    unless(sel printf("Nothing selected\n"))
    foreach(obj sel
      when(obj~>objType == "inst"
        printf("%-10s %s/%s/%s  at %L %s\n"
               obj~>name obj~>libName obj~>cellName obj~>viewName
               obj~>xy obj~>orient)
        when(cdfGetInstCDF(obj)
          foreach(p cdfGetInstCDF(obj)~>parameters
            when(p~>value && p~>value != "" && p~>paramType != "button"
              printf("    %-12s = %L\n" p~>name p~>value))))))
    length(sel)))

;; Open a cellview read-only in a new window
procedure(vagOpen(lib cell @optional (view "schematic"))
  geOpen(?lib lib ?cell cell ?view view ?mode "r"))

;; Reload every .il file in $VAG_SKILL_DIR (useful while developing)
procedure(vagReloadSkill()
  let((dir)
    dir = getShellEnvVar("VAG_SKILL_DIR")
    if(dir then
      foreach(f setof(x getDirFiles(dir) rexMatchp("\\.il$" x))
        unless(member(f '("run_maestro.il" "batch_wrapper.il"))
          printf("loading %s\n" f)
          loadi(strcat(dir "/" f))))
    else
      warn("VAG_SKILL_DIR not set\n"))))

;; Write a visible marker into CDS.log (helps find your section later)
procedure(vagLogMarker(text)
  printf("\n########## %s : %s ##########\n" getCurrentTime() text))

;; Bindkeys (schematic editor). Change keys to taste.
hiSetBindKey("Schematics" "Ctrl Shift<Key>i" "vagPrintSelected()")

printf("ciw_helpers.il loaded: vagPrintSelected (Ctrl+Shift+i) vagOpen vagReloadSkill vagLogMarker\n")
