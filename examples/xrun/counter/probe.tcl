# probe.tcl : record all signals into an SHM database, run to the end, exit
database -open waves -shm -default
probe -create tb_counter -all -depth all -database waves
run
exit
