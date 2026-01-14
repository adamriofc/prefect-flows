#!/bin/bash
# ========================================
# Prefect Cloud Helper for OpenCode
# ========================================
# Location: D:\Projects\PrefectFlows\prefect-helper.sh
# WSL Path: /mnt/d/Projects/PrefectFlows/prefect-helper.sh
#
# Usage: bash prefect-helper.sh <command>

PREFECT_BIN=~/.local/bin/prefect
FLOWS_DIR=/mnt/d/Projects/PrefectFlows

case "$1" in
  "status")
    echo "=== Prefect Cloud Status ==="
    $PREFECT_BIN version
    echo ""
    echo "Dashboard: https://app.prefect.cloud"
    ;;
  "runs")
    echo "=== Recent Flow Runs ==="
    $PREFECT_BIN flow-run ls --limit 10
    ;;
  "flows")
    echo "=== Registered Flows ==="
    $PREFECT_BIN flow ls
    ;;
  "deployments")
    echo "=== Deployments ==="
    $PREFECT_BIN deployment ls
    ;;
  "run")
    if [ -z "$2" ]; then
      echo "Usage: prefect-helper.sh run <flow_file.py>"
      exit 1
    fi
    echo "=== Running Flow: $2 ==="
    python3 "$2"
    ;;
  "serve")
    if [ -z "$2" ]; then
      echo "Usage: prefect-helper.sh serve <flow_file.py>"
      echo "This will start a long-running process that serves the flow."
      echo "The flow can then be triggered from Prefect Cloud UI!"
      exit 1
    fi
    echo "=== Serving Flow: $2 ==="
    echo "Flow will be available in Prefect Cloud -> Deployments"
    echo "Press Ctrl+C to stop."
    python3 "$2"
    ;;
  "serve-bg")
    if [ -z "$2" ]; then
      echo "Usage: prefect-helper.sh serve-bg <flow_file.py>"
      echo "This runs the serve process in background."
      exit 1
    fi
    echo "=== Starting Flow Server in Background ==="
    nohup python3 "$FLOWS_DIR/$2" > ~/prefect-serve-$2.log 2>&1 &
    echo "PID: $!"
    echo "Log: ~/prefect-serve-$2.log"
    echo "Flow will be available in Prefect Cloud -> Deployments"
    ;;
  "serve-stop")
    echo "=== Stopping All Flow Servers ==="
    pkill -f "prefect.*serve" 2>/dev/null || true
    pkill -f "triggerable_flow.py" 2>/dev/null || true
    echo "Done."
    ;;
  "trigger-server")
    echo "=== Starting Remote Trigger Server ==="
    python3 "$FLOWS_DIR/remote_trigger_server.py"
    ;;
  "trigger-server-bg")
    echo "=== Starting Remote Trigger Server in Background ==="
    nohup python3 "$FLOWS_DIR/remote_trigger_server.py" > ~/prefect-trigger-server.log 2>&1 &
    echo "PID: $!"
    echo "Log: ~/prefect-trigger-server.log"
    echo "Server: http://localhost:8080"
    ;;
  "deploy")
    if [ -z "$2" ]; then
      echo "Usage: prefect-helper.sh deploy <flow_file.py>"
      exit 1
    fi
    echo "=== Deploying Flow: $2 ==="
    $PREFECT_BIN deploy "$2"
    ;;
  "logs")
    if [ -z "$2" ]; then
      echo "Usage: prefect-helper.sh logs <flow-run-id>"
      exit 1
    fi
    $PREFECT_BIN flow-run logs "$2"
    ;;
  "dashboard")
    echo "=========================================="
    echo "  Prefect Cloud Dashboard"
    echo "=========================================="
    echo ""
    echo "  URL: https://app.prefect.cloud"
    echo ""
    echo "  Account: adamriofc"
    echo "  Workspace: default"
    echo ""
    echo "=========================================="
    ;;
  "help"|*)
    echo "=========================================="
    echo "  Prefect Cloud Helper for OpenCode"
    echo "=========================================="
    echo ""
    echo "BASIC COMMANDS:"
    echo "  status         - Check connection to Prefect Cloud"
    echo "  runs           - List recent flow runs"
    echo "  flows          - List registered flows"
    echo "  deployments    - List deployments"
    echo "  run <file>     - Run a flow file directly"
    echo "  logs <id>      - View flow run logs"
    echo "  dashboard      - Show dashboard URL"
    echo ""
    echo "CLOUD UI TRIGGER (FREE!):"
    echo "  serve <file>   - Serve flow (can trigger from Cloud UI)"
    echo "  serve-bg <file>- Serve flow in background"
    echo "  serve-stop     - Stop all serve processes"
    echo ""
    echo "REMOTE API TRIGGER:"
    echo "  trigger-server    - Start HTTP trigger server"
    echo "  trigger-server-bg - Start trigger server in background"
    echo ""
    echo "EXAMPLES:"
    echo "  bash prefect-helper.sh run hello_flow.py"
    echo "  bash prefect-helper.sh serve triggerable_flow.py"
    echo "  bash prefect-helper.sh trigger-server"
    echo ""
    echo "=========================================="
    ;;
esac
