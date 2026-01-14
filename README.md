# Prefect Cloud Integration for OpenCode

## Quick Reference

| Component | Location |
|-----------|----------|
| **Dashboard** | https://app.prefect.cloud |
| **Account** | adamriofc |
| **Workspace** | default |
| **Client** | WSL (`~/.local/bin/prefect`) |
| **Flows Folder** | `D:\Projects\PrefectFlows` |
| **WSL Path** | `/mnt/d/Projects/PrefectFlows` |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PREFECT CLOUD                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Dashboard: https://app.prefect.cloud                                 │  │
│  │  - Monitoring & Logs                                                  │  │
│  │  - Flow Run History                                                   │  │
│  │  - Notifications                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ↕ API                                    │
└────────────────────────────────────│────────────────────────────────────────┘
                                     │
┌────────────────────────────────────│────────────────────────────────────────┐
│  WSL (PC Lokal)                    ↓                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Prefect Client (authenticated)                                       │  │
│  │  - Runs Python scripts locally                                        │  │
│  │  - Sends results to Cloud                                             │  │
│  │  - Access to local files (D:\, C:\)                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Commands

### Run Flow Directly
```bash
# Via WSL
cd /mnt/d/Projects/PrefectFlows
python3 hello_flow.py

# Via OpenCode/Windows
wsl -- bash -l -c "cd /mnt/d/Projects/PrefectFlows && python3 hello_flow.py"
```

### Using Helper Script
```bash
# Check status
bash prefect-helper.sh status

# List recent runs
bash prefect-helper.sh runs

# Run a flow
bash prefect-helper.sh run hello_flow.py

# Show help
bash prefect-helper.sh help
```

### Prefect CLI (Direct)
```bash
# List flow runs
~/.local/bin/prefect flow-run ls

# View logs
~/.local/bin/prefect flow-run logs <run-id>

# Check version/connection
~/.local/bin/prefect version
```

## Environment Variables

Stored in `~/.bashrc`:
```bash
export PREFECT_API_URL="https://api.prefect.cloud/api/accounts/..."
export PREFECT_API_KEY="pnu_..."
```

## Flow Example

```python
from prefect import flow, task

@task
def say_hello(name: str):
    print(f"Hello, {name}!")
    return f"Hello, {name}!"

@flow(name="My Flow", log_prints=True)
def my_flow(name: str = "World"):
    result = say_hello(name)
    return result

if __name__ == "__main__":
    my_flow()
```

## Scheduled Jobs (Serve Mode)

For scheduled/recurring jobs, use `.serve()`:

```python
from prefect import flow

@flow
def my_scheduled_flow():
    print("Running scheduled task...")

if __name__ == "__main__":
    # This will keep running and execute on schedule
    my_scheduled_flow.serve(
        name="my-scheduled-deployment",
        cron="0 9 * * *",  # Every day at 9 AM
    )
```

Run with:
```bash
# This is a long-running process
python3 my_scheduled_flow.py
```

## Troubleshooting

### Check Connection
```bash
~/.local/bin/prefect version
# Should show: Server type: cloud
```

### Re-login if needed
```bash
~/.local/bin/prefect cloud login -k <API_KEY> -w adamriofc/default
```

### View Dashboard
Open: https://app.prefect.cloud

## Files

```
D:\Projects\PrefectFlows\
├── hello_flow.py        # Sample flow
├── prefect-helper.sh    # Helper script
└── README.md            # This file
```
