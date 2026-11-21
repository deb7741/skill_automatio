# probe.tcl : digital-side probes for the AMS run
database -open waves -shm -default
probe -create tb_dac -all -depth all -database waves
run
exit
