#!/bin/bash
cd "$(dirname "$0")" || exit 1
mkdir -p logs
./venv/bin/python run_kubo.py >> logs/task_kubo.log 2>&1
