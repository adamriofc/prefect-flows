"""
Sample Prefect Flow - Hello World
Location: D:\Projects\PrefectFlows\hello_flow.py
WSL Path: /mnt/d/Projects/PrefectFlows/hello_flow.py

Run with: prefect run hello_flow.py
"""

from prefect import flow, task
from datetime import datetime


@task(log_prints=True)
def say_hello(name: str) -> str:
    """A simple task that greets someone."""
    message = f"Hello, {name}! Welcome to Prefect 3!"
    print(message)
    return message


@task(log_prints=True)
def get_current_time() -> str:
    """Get the current timestamp."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current time: {now}")
    return now


@flow(name="Hello World Flow", log_prints=True)
def hello_flow(name: str = "OpenCode User"):
    """
    A simple hello world flow demonstrating Prefect 3 basics.
    
    Args:
        name: The name to greet (default: OpenCode User)
    """
    print("=" * 50)
    print("Starting Hello World Flow")
    print("=" * 50)
    
    # Run tasks
    greeting = say_hello(name)
    timestamp = get_current_time()
    
    print(f"\nFlow completed successfully!")
    print(f"Greeting: {greeting}")
    print(f"Timestamp: {timestamp}")
    
    return {"greeting": greeting, "timestamp": timestamp}


if __name__ == "__main__":
    # Run the flow directly
    result = hello_flow()
    print(f"\nResult: {result}")
