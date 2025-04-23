#!/bin/bash
# This script runs the Wokwi CLI to simulate a senario file and save the output to a file.
# It sets the Wokwi CLI token and runs the simulation with a timeout of 8 minutes.
# The output is saved to out.txt in the current directory.

#http://wokwi.com/dashboard/ci
export WOKWI_CLI_TOKEN=
# Run Wokwi simulation in the background
wokwi-cli simulate --scenario ../scenario.yaml --serial-log-file out.txt --timeout 86400000 &

# Run FastAPI server in the background
# .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8001 &
uvicorn main:app --reload --host 0.0.0.0 --port 8001 &

# Wait for all background processes to finish
wait