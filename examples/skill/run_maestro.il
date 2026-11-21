;; =====================================================================
;; run_maestro.il : batch entry point for maestro runs
;;
;;   export VAG_SKILL_DIR=/path/to/repo/examples/skill
;;   export VAG_LIB=myLib VAG_CELL=myTb VAG_VARS="rval=2k" VAG_CSV=./out/myTb.csv
;;   virtuoso -nograph -restore $VAG_SKILL_DIR/run_maestro.il -log run_maestro.log
;;   grep BATCH_STATUS run_maestro.log
;; =====================================================================
let((dir hist)
  dir = getShellEnvVar("VAG_SKILL_DIR") || "."
  load(strcat(dir "/maestro_batch.il"))
  hist = vagMaeRunFromEnv()
  printf("BATCH_HISTORY: %L\n" hist)
  printf("BATCH_STATUS: %s\n" if(hist "PASS" "FAIL"))
  exit(if(hist 0 1)))
