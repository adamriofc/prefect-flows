# Prefect Flows

Workflow orchestration flows managed by OpenCode with full Prefect Cloud integration.

## Quick Start

```bash
# Run a flow locally
wsl -- bash -l -c "cd /mnt/d/Projects/PrefectFlows && python3 hello_flow.py"

# Start triggerable flow server
wsl -- bash -l -c "cd /mnt/d/Projects/PrefectFlows && python3 triggerable_flow.py"

# Use PrefectManager
wsl -- bash -l -c "cd /mnt/d/Projects/PrefectFlows && python3 lib/prefect_manager.py health"
```

## Architecture

```
+-----------------------------------------------------------------------------+
|                           PREFECT CLOUD                                     |
|  Dashboard: https://app.prefect.cloud                                       |
+-----------------------------------------------------------------------------+
                                    |
                                    | API
                                    v
+-----------------------------------------------------------------------------+
|  OPENCODE (This PC)                                                         |
|  +-----------------------------------------------------------------------+  |
|  |  Prefect MCP Server                                                   |  |
|  |  - Native integration for AI assistant                                |  |
|  |  - Full control over Prefect Cloud resources                          |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |  GitHub Integration                                                   |  |
|  |  - Repo: https://github.com/adamriofc/prefect-flows                   |  |
|  |  - Auto-deploy on push via GitHub Actions                             |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  Project: D:\Projects\PrefectFlows                                          |
+-----------------------------------------------------------------------------+
```

## Files

| File | Description |
|------|-------------|
| `hello_flow.py` | Simple Hello World flow for testing |
| `triggerable_flow.py` | Flow with `.serve()` - triggerable from Cloud UI |
| `remote_trigger_server.py` | HTTP API server for external triggers |
| `lib/prefect_manager.py` | Python module for programmatic Prefect management |
| `prefect-helper.sh` | Bash helper script for common operations |
| `prefect.yaml` | Deployment configuration for GitOps |

## Integration Methods

### 1. Prefect MCP Server (Recommended)

OpenCode has native integration with Prefect Cloud via MCP:

```json
// ~/.config/opencode/opencode.json
{
  "mcp": {
    "prefect": {
      "type": "local",
      "command": ["uvx", "--from", "prefect-mcp", "prefect-mcp-server"],
      "environment": {
        "PREFECT_API_URL": "your-api-url",
        "PREFECT_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 2. PrefectManager Module

```python
from lib import PrefectManager

manager = PrefectManager()

# List deployments
for d in manager.list_deployments_sync():
    print(f"{d.flow_name}/{d.name}")

# Trigger a deployment
result = manager.trigger_deployment_sync(
    "My Flow/my-deployment",
    parameters={"key": "value"}
)
print(f"Started: {result.url}")

# Wait for completion
final = manager.wait_for_completion_sync(result.id)
print(f"State: {final.state}")
```

### 3. CLI Interface

```bash
# Health check
python3 lib/prefect_manager.py health

# List deployments
python3 lib/prefect_manager.py deployments

# List recent runs
python3 lib/prefect_manager.py runs 10

# Trigger deployment
python3 lib/prefect_manager.py trigger "Hello World Flow/hello-flow"

# Get run status
python3 lib/prefect_manager.py status <flow-run-id>

# Get dashboard URLs
python3 lib/prefect_manager.py urls
```

### 4. Prefect CLI

```bash
# List deployments
prefect deployment ls

# Trigger deployment
prefect deployment run 'Hello World Flow/hello-flow'

# List flow runs
prefect flow-run ls

# Get logs
prefect flow-run logs <flow-run-id>
```

### 5. REST API

```bash
PREFECT_API_URL="https://api.prefect.cloud/api/accounts/YOUR_ACCOUNT/workspaces/YOUR_WORKSPACE"
PREFECT_API_KEY="pnu_YOUR_API_KEY"

# List deployments
curl -X POST "$PREFECT_API_URL/deployments/filter" \
  -H "Authorization: Bearer $PREFECT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# Trigger deployment
curl -X POST "$PREFECT_API_URL/deployments/DEPLOYMENT_ID/create_flow_run" \
  -H "Authorization: Bearer $PREFECT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"key": "value"}}'
```

## Prefect Cloud Blocks

| Block | Name | Purpose |
|-------|------|---------|
| GitHub Credentials | `opencode-github` | Auth for private repos |
| GitHub Repository | `prefect-flows-repo` | Link to this repo |

## GitHub Actions

Push to `master` branch auto-deploys flows to Prefect Cloud.

Required GitHub Secrets:
- `PREFECT_API_KEY`: Prefect Cloud API key
- `PREFECT_API_URL`: Prefect Cloud workspace URL
- `PREFECT_WORKSPACE`: Workspace identifier (account/workspace)

## Environment Variables

```bash
# Required for Prefect Cloud access
export PREFECT_API_URL="https://api.prefect.cloud/api/accounts/YOUR_ACCOUNT/workspaces/YOUR_WORKSPACE"
export PREFECT_API_KEY="pnu_YOUR_API_KEY"
```

## Links

- **Prefect Cloud Dashboard**: https://app.prefect.cloud
- **GitHub Repository**: https://github.com/adamriofc/prefect-flows
- **Prefect Documentation**: https://docs.prefect.io

---

*Managed by OpenCode AI Assistant*
