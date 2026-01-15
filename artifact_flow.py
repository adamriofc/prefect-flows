"""
Artifact Demo Flow
==================
Demonstrates generating rich markdown reports visible in OpenCode/Prefect UI.
"""

from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
from datetime import datetime

@task
def analyze_data():
    """Simulate data analysis."""
    return {"rows": 1250, "quality": "98.5%", "errors": 0}

@flow(name="Artifact Demo", log_prints=True)
def artifact_flow():
    print("Starting analysis...")
    data = analyze_data()
    
    # Create Markdown Report
    report = f"""
# 📊 Data Analysis Report
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
| Metric | Value |
| :--- | :--- |
| **Rows** | `{data['rows']}` |
| **Quality** | **{data['quality']}** |
| **Errors** | {data['errors']} |

## Status
✅ **Analysis Complete**
    """
    
    # Publish to Prefect Cloud
    create_markdown_artifact(
        key="analysis-report",
        markdown=report,
        description="Automated Analysis Report"
    )
    print("Artifact published: analysis-report")
    return "Success"

if __name__ == "__main__":
    # Local test
    artifact_flow()
