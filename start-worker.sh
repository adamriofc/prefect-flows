#!/bin/bash
# Start a local Prefect Worker
# This allows you to run flows on this machine (Unlimited Compute)
# bypassing the 500 minutes/month limit of Managed pools.
#
# Prerequisite: You must have a 'process' type work pool.
# Usage: ./start-worker.sh [pool-name]

POOL_NAME=${1:-"local-process-pool"}

echo "==================================================="
echo "   Prefect Local Worker Launcher"
echo "==================================================="
echo "Target Pool: $POOL_NAME"
echo ""

# Check for uv/pip
if command -v uv >/dev/null 2>&1; then
    CMD="uv run prefect"
else
    CMD="python3 -m prefect"
fi

echo "Starting worker..."
$CMD worker start --pool "$POOL_NAME"
