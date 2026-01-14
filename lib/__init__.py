"""
Prefect Flows Library
====================

Utility modules for Prefect Cloud management.

Usage:
    from lib import PrefectManager
    
    manager = PrefectManager()
    deployments = manager.list_deployments_sync()
"""

from .prefect_manager import (
    PrefectManager,
    FlowRunResult,
    DeploymentInfo,
    quick_trigger,
    quick_status,
    list_recent_runs,
)

__all__ = [
    "PrefectManager",
    "FlowRunResult",
    "DeploymentInfo",
    "quick_trigger",
    "quick_status",
    "list_recent_runs",
]

__version__ = "1.0.0"
