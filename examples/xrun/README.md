# Xcelium / xrun example: counter

```bash
cd counter
./run.sh            # batch, waves in waves.shm
./run.sh gui        # SimVision
./run.sh cov        # coverage
./run.sh seeds 8    # build once, 8 seeds in parallel

# Regression with JUnit output
python3 ../../python/xrun_regression.py tests.json --jobs 4 --junit out/junit.xml
```

The testbench prints `TEST PASSED` / `TEST FAILED`, so scripts don't depend on exit codes alone.
