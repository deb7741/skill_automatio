;; =====================================================================
;; batch_wrapper.il : CI-safe pattern for running any SKILL task in
;; "virtuoso -nograph". Always prints a BATCH_STATUS marker and exits,
;; even when the task throws an error.
;;
;;   export VAG_SKILL_DIR=/path/to/repo/examples/skill
;;   export VAG_LIB=myLib
;;   virtuoso -nograph -restore $VAG_SKILL_DIR/batch_wrapper.il -log batch.log
;; =====================================================================
let((dir lib ok)
  dir = getShellEnvVar("VAG_SKILL_DIR") || "."
  lib = getShellEnvVar("VAG_LIB") || "myLib"

  ok = errset(
    progn(
      load(strcat(dir "/create_testbench.il"))
      load(strcat(dir "/lib_utils.il"))
      ;; ---- the actual task(s) ----
      vagCreateRcTestbench(lib "rc_tb")
      vagReportLibrary(lib "./library_report.csv")
      t)
    t)

  printf("BATCH_STATUS: %s\n" if(ok && car(ok) "PASS" "FAIL"))
  exit(if(ok && car(ok) 0 1)))
