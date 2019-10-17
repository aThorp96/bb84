#!/bin/bash
# This script runs alice.py and bob.py a number of times and records the output.
# It was designed to get some statistics on error the error rate of the key exchage,
# but it could be used as an example of how one might setup simulaqron and run alice.py and bob.py

RUNS=1000
LOG="results.csv"

if [ "$VIRTUAL_ENV" == "" ]; then
	echo "No virtual environment"
	exit 0
fi 

simulaqron reset --force
simulaqron start --force
simulaqron set max-qubits 128
simulaqron set log-level 10
simulaqron stop
simulaqron start --force

echo "Simulaqron reset"

for i in $(seq $RUNS); do
	# Mark itteration and get timestamp
	START=$(date +%s%3N)

	# Run program
	python3 bob.py &
	RES=$(python3 alice.py)

	# Wait for programs to finish and get timestamp
	while [[ "$(jobs)" != "" ]]; do
		WAITING="TRUE"	
	done
	WAITING="FALSE"

	TIME=$(( $(date +%s%3N) - $START ))
	echo "$i, $RES, $TIME" | tee -a $LOG

done

