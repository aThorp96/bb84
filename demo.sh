#!/bin/bash

# This is a demo to show example output of running `alice.py` and `bob.py`

simulaqron reset --force
simulaqron start --force
simulaqron set max-qubits 128
simulaqron stop
simulaqron start --force

echo "Simulaqron reset"
# Run program
python3 bob.py &
python3 alice.py

# Wait for programs to finish and get timestamp
while [[ "$(jobs)" != "" ]]; do
    sleep 0.5s
done

