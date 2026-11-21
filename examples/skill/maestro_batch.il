;; =====================================================================
;; maestro_batch.il : run an ADE Explorer/Assembler (maestro) setup in
;; batch, optionally override variables, export results to CSV.
;;
;; Interactive:  load("maestro_batch.il")
;;               vagMaeRun(?lib "myLib" ?cell "myTb" ?vars '(("rval" "2k")) ?csv "r.csv")
;; Batch:        see run_maestro.il  ->  virtuoso -nograph -restore run_maestro.il
;;
;; Tested: IC6.1.8 ISR / IC23.1. Function keywords per the Virtuoso ADE
;; SKILL Reference; check the SKILL API Finder ("mae") for your release.
;; =====================================================================

;; ---------------------------------------------------------------------
;; vagMaeRun(?lib ?cell [?view "maestro"] [?vars ((name value) ...)]
;;           [?tests (testName ...)] [?csv file] [?exportView "Detail"]
;;           [?runMode string] [?save nil])
;;   => history name (string) on success, nil on failure
;; ---------------------------------------------------------------------
procedure(vagMaeRun(@key lib cell (view "maestro") (vars nil) (tests nil)
                         (csv nil) (exportView "Detail") (runMode nil)
                         (save nil))
  let((sess hist res)
    unless(lib && cell error("vagMaeRun: ?lib and ?cell are required\n"))

    res = errset(
      progn(
        sess = maeOpenSetup(lib cell view ?mode "a")
        unless(sess error("maeOpenSetup failed for %s/%s/%s\n" lib cell view))
        printf("vagMaeRun: opened %s/%s/%s as session %L\n" lib cell view sess)

        ;; global variable overrides
        foreach(v vars
          printf("vagMaeRun: %s = %s\n" car(v) cadr(v))
          maeSetVar(car(v) cadr(v) ?session sess))

        ;; restrict to some tests (others keep their saved enable state)
        when(tests maeSetSetup(?tests tests ?enabled t ?session sess))

        ;; run and wait
        hist = if(runMode
                  maeRunSimulation(?session sess ?runMode runMode)
                  maeRunSimulation(?session sess))
        printf("vagMaeRun: started history %L\n" hist)
        maeWaitUntilDone('All)

        ;; export
        when(csv && hist
          printf("vagMaeRun: exported %L\n"
                 maeExportOutputView(?session sess ?fileName csv
                                     ?view exportView ?historyName hist)))
        when(save maeSaveSetup(?session sess))
        hist)
      t)                                   ; t = print error messages

    ;; always try to close the session
    when(sess errset(maeCloseSession(?session sess ?forceClose t) nil))
    if(res then car(res) else nil)))

;; ---------------------------------------------------------------------
;; vagMaeRunFromEnv() : read settings from environment variables so a
;; Python/shell driver can call the same batch script with new values.
;;   VAG_LIB, VAG_CELL           (required)
;;   VAG_VARS="rval=2k,cval=1n"  (optional)
;;   VAG_CSV="./out/results.csv" (optional)
;;   VAG_RUNMODE="Single Run, Sweeps and Corners" (optional)
;; ---------------------------------------------------------------------
procedure(vagMaeRunFromEnv()
  let((lib cell varsStr vars csv runMode)
    lib     = getShellEnvVar("VAG_LIB")
    cell    = getShellEnvVar("VAG_CELL")
    varsStr = getShellEnvVar("VAG_VARS")
    csv     = getShellEnvVar("VAG_CSV")
    runMode = getShellEnvVar("VAG_RUNMODE")
    when(varsStr
      vars = foreach(mapcar kv parseString(varsStr ",")
               parseString(kv "=")))
    vagMaeRun(?lib lib ?cell cell ?vars vars ?csv csv ?runMode runMode)))

printf("maestro_batch.il loaded: vagMaeRun vagMaeRunFromEnv\n")
