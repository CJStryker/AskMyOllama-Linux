#!/usr/bin/env bash
read -p "Simulate task: " TASK

ask --en "
Simulate the following Linux task.
Do NOT give commands.
Explain what would likely happen step by step.
Task:
$TASK
"
