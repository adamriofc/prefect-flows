"""
Triggerable Flow - Can be triggered from Prefect Cloud UI!
Location: D:\Projects\PrefectFlows\triggerable_flow.py
WSL Path: /mnt/d/Projects/PrefectFlows/triggerable_flow.py

How to use:
1. Run this script: python3 triggerable_flow.py
2. It will register as a Deployment in Prefect Cloud
3. Go to Prefect Cloud UI -> Deployments -> Click "Run"
4. The flow will execute on your PC!

Note: This script must keep running for the trigger to work.
"""

from prefect import flow, task
from datetime import datetime


@task(log_prints=True)
def process_data(data: str) -> str:
    """Process some data."""
    result = f"Processed: {data.upper()}"
    print(result)
    return result


@task(log_prints=True)
def get_timestamp() -> str:
    """Get current timestamp."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Timestamp: {now}")
    return now


@flow(name="Triggerable Flow", log_prints=True)
def triggerable_flow(data: str = "Hello from Cloud UI"):
    """
    A flow that can be triggered from Prefect Cloud UI.
    
    Args:
        data: Input data to process
    """
    print("=" * 50)
    print("Flow triggered!")
    print("=" * 50)
    
    result = process_data(data)
    timestamp = get_timestamp()
    
    print(f"\nFlow completed!")
    print(f"Result: {result}")
    print(f"Time: {timestamp}")
    
    return {"result": result, "timestamp": timestamp}


if __name__ == "__main__":
    # This creates a Deployment that can be triggered from Cloud UI
    # The script must keep running for triggers to work
    print("=" * 60)
    print("Starting Triggerable Flow Server")
    print("=" * 60)
    print("")
    print("This flow is now available in Prefect Cloud!")
    print("Go to: https://app.prefect.cloud")
    print("Navigate to: Deployments -> 'Triggerable Flow'")
    print("Click 'Run' to trigger this flow remotely!")
    print("")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)
    
    triggerable_flow.serve(
        name="cloud-triggerable",
        tags=["opencode", "triggerable"],
        description="Flow that can be triggered from Prefect Cloud UI",
        version="1.0.0",
    )
