"""
PrefectManager - Complete Prefect Cloud Management Module
=========================================================

This module provides a comprehensive Python interface for managing Prefect Cloud
resources programmatically. Designed for use by OpenCode and automation scripts.

Features:
- Full deployment management (list, trigger, pause, resume)
- Flow run monitoring and control
- Block management (create, read, update, delete)
- Variable management
- Async and sync interfaces

Usage:
    from lib.prefect_manager import PrefectManager
    
    manager = PrefectManager()
    
    # Sync usage
    deployments = manager.list_deployments_sync()
    
    # Async usage
    import asyncio
    deployments = asyncio.run(manager.list_deployments())

Author: OpenCode AI Assistant
Created: 2026-01-15
"""

import os
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

# Prefect imports
from prefect import get_client
from prefect.client.orchestration import get_client as get_sync_client
from prefect.deployments import run_deployment
from prefect.variables import Variable
from prefect.blocks.system import Secret
from prefect.client.schemas.filters import (
    DeploymentFilter,
    DeploymentFilterName,
    FlowRunFilter,
    FlowRunFilterState,
    FlowRunFilterStateName,
    FlowRunFilterStateType,
)
from prefect.client.schemas.sorting import FlowRunSort, DeploymentSort
from prefect.client.schemas.objects import FlowRun, Deployment
from prefect.client.schemas.actions import DeploymentScheduleCreate
from prefect.client.schemas.schedules import IntervalSchedule, CronSchedule
from prefect.events.schemas.automations import EventTrigger, Posture, AutomationCore
from prefect.events.actions import RunDeployment as RunDeploymentAction


@dataclass
class FlowRunResult:
    """Result container for flow run information."""
    id: str
    name: str
    state: str
    state_type: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    parameters: Dict[str, Any]
    url: str


@dataclass
class DeploymentInfo:
    """Container for deployment information."""
    id: str
    name: str
    flow_name: str
    description: Optional[str]
    tags: List[str]
    is_schedule_active: bool
    url: str


class PrefectManager:
    """
    Comprehensive Prefect Cloud management class.
    
    Provides both async and sync interfaces for managing:
    - Deployments
    - Flow runs
    - Blocks
    - Variables
    
    Example:
        manager = PrefectManager()
        
        # List all deployments
        deps = manager.list_deployments_sync()
        for d in deps:
            print(f"{d.name}: {d.flow_name}")
        
        # Trigger a deployment
        run = manager.trigger_deployment_sync("My Flow/my-deployment")
        print(f"Started run: {run.id}")
        
        # Wait for completion
        result = manager.wait_for_completion_sync(run.id, timeout=300)
        print(f"Completed with state: {result.state}")
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize PrefectManager.
        
        Args:
            api_url: Prefect Cloud API URL. If not provided, uses PREFECT_API_URL env var.
            api_key: Prefect Cloud API key. If not provided, uses PREFECT_API_KEY env var.
        """
        if api_url:
            os.environ["PREFECT_API_URL"] = api_url
        if api_key:
            os.environ["PREFECT_API_KEY"] = api_key
        
        self._account_id = self._extract_account_id()
        self._workspace_id = self._extract_workspace_id()
    
    def _extract_account_id(self) -> Optional[str]:
        """Extract account ID from API URL."""
        url = os.environ.get("PREFECT_API_URL", "")
        if "/accounts/" in url:
            parts = url.split("/accounts/")[1].split("/")
            return parts[0] if parts else None
        return None
    
    def _extract_workspace_id(self) -> Optional[str]:
        """Extract workspace ID from API URL."""
        url = os.environ.get("PREFECT_API_URL", "")
        if "/workspaces/" in url:
            parts = url.split("/workspaces/")[1].split("/")
            return parts[0] if parts else None
        return None
    
    @property
    def cloud_url(self) -> str:
        """Get Prefect Cloud dashboard URL."""
        if self._account_id and self._workspace_id:
            return f"https://app.prefect.cloud/account/{self._account_id}/workspace/{self._workspace_id}"
        return "https://app.prefect.cloud"
    
    # =========================================================================
    # DEPLOYMENT MANAGEMENT
    # =========================================================================
    
    async def list_deployments(
        self,
        name_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[DeploymentInfo]:
        """
        List all deployments with optional filtering.
        
        Args:
            name_filter: Filter by deployment name (supports wildcards)
            tags: Filter by tags (all tags must match)
            limit: Maximum number of results
            
        Returns:
            List of DeploymentInfo objects
        """
        async with get_client() as client:
            filter_obj = None
            if name_filter:
                filter_obj = DeploymentFilter(
                    name=DeploymentFilterName(like_=name_filter)
                )
            
            deployments = await client.read_deployments(
                deployment_filter=filter_obj,
                limit=limit
            )
            
            results = []
            for d in deployments:
                # Get flow name
                flow = await client.read_flow(d.flow_id)
                
                results.append(DeploymentInfo(
                    id=str(d.id),
                    name=d.name,
                    flow_name=flow.name,
                    description=d.description,
                    tags=list(d.tags) if d.tags else [],
                    is_schedule_active=getattr(d, 'is_schedule_active', True),
                    url=f"{self.cloud_url}/deployments/deployment/{d.id}"
                ))
            
            return results
    
    def list_deployments_sync(self, **kwargs) -> List[DeploymentInfo]:
        """Synchronous wrapper for list_deployments."""
        return asyncio.run(self.list_deployments(**kwargs))
    
    async def trigger_deployment(
        self,
        deployment_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        wait: bool = False,
        timeout: int = 300
    ) -> FlowRunResult:
        """
        Trigger a deployment run.
        
        Args:
            deployment_name: Full deployment name (format: "Flow Name/deployment-name")
            parameters: Optional parameters to pass to the flow
            tags: Optional tags to add to the run
            wait: If True, wait for the run to complete
            timeout: Timeout in seconds when waiting (default: 300)
            
        Returns:
            FlowRunResult with run information
        """
        flow_run = await run_deployment(
            name=deployment_name,
            parameters=parameters or {},
            tags=tags,
            timeout=timeout if wait else 0
        )
        
        return FlowRunResult(
            id=str(flow_run.id),
            name=flow_run.name,
            state=flow_run.state.name if flow_run.state else "Unknown",
            state_type=str(flow_run.state.type) if flow_run.state else "Unknown",
            start_time=flow_run.start_time,
            end_time=flow_run.end_time,
            parameters=flow_run.parameters or {},
            url=f"{self.cloud_url}/runs/flow-run/{flow_run.id}"
        )
    
    def trigger_deployment_sync(self, deployment_name: str, **kwargs) -> FlowRunResult:
        """Synchronous wrapper for trigger_deployment."""
        return asyncio.run(self.trigger_deployment(deployment_name, **kwargs))
    
    async def set_deployment_schedule(
        self,
        deployment_id: str,
        cron: Optional[str] = None,
        interval: Optional[int] = None
    ) -> None:
        """
        Set deployment schedule (replaces existing).
        
        Args:
            deployment_id: Deployment UUID
            cron: Cron expression (e.g. "0 9 * * *")
            interval: Interval in seconds
        """
        from prefect.client.schemas.actions import DeploymentUpdate, DeploymentScheduleCreate
        
        schedule_config = None
        if cron:
            schedule_config = CronSchedule(cron=cron)
        elif interval:
            schedule_config = IntervalSchedule(interval=timedelta(seconds=interval))
            
        async with get_client() as client:
            await client.update_deployment(
                deployment_id=deployment_id,
                deployment=DeploymentUpdate(
                    schedules=[
                        {
                            "schedule": schedule_config,
                            "active": True
                        }
                    ]
                )
            )

    def set_deployment_schedule_sync(self, **kwargs) -> None:
        """Synchronous wrapper for set_deployment_schedule."""
        return asyncio.run(self.set_deployment_schedule(**kwargs))
    
    # =========================================================================
    # FLOW RUN MANAGEMENT
    # =========================================================================
    
    async def get_flow_run(self, flow_run_id: str) -> FlowRunResult:
        """
        Get details of a specific flow run.
        
        Args:
            flow_run_id: UUID of the flow run
            
        Returns:
            FlowRunResult with run information
        """
        async with get_client() as client:
            run = await client.read_flow_run(flow_run_id)
            
            return FlowRunResult(
                id=str(run.id),
                name=run.name,
                state=run.state.name if run.state else "Unknown",
                state_type=str(run.state.type) if run.state else "Unknown",
                start_time=run.start_time,
                end_time=run.end_time,
                parameters=run.parameters or {},
                url=f"{self.cloud_url}/runs/flow-run/{run.id}"
            )
    
    def get_flow_run_sync(self, flow_run_id: str) -> FlowRunResult:
        """Synchronous wrapper for get_flow_run."""
        return asyncio.run(self.get_flow_run(flow_run_id))
    
    async def list_flow_runs(
        self,
        states: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[FlowRunResult]:
        """
        List recent flow runs.
        
        Args:
            states: Filter by state names (e.g., ["Completed", "Failed"])
            limit: Maximum number of results
            
        Returns:
            List of FlowRunResult objects
        """
        async with get_client() as client:
            filter_obj = None
            if states:
                filter_obj = FlowRunFilter(
                    state=FlowRunFilterState(
                        name=FlowRunFilterStateName(any_=states)
                    )
                )
            
            runs = await client.read_flow_runs(
                flow_run_filter=filter_obj,
                sort=FlowRunSort.START_TIME_DESC,
                limit=limit
            )
            
            return [
                FlowRunResult(
                    id=str(r.id),
                    name=r.name,
                    state=r.state.name if r.state else "Unknown",
                    state_type=str(r.state.type) if r.state else "Unknown",
                    start_time=r.start_time,
                    end_time=r.end_time,
                    parameters=r.parameters or {},
                    url=f"{self.cloud_url}/runs/flow-run/{r.id}"
                )
                for r in runs
            ]
    
    def list_flow_runs_sync(self, **kwargs) -> List[FlowRunResult]:
        """Synchronous wrapper for list_flow_runs."""
        return asyncio.run(self.list_flow_runs(**kwargs))
    
    async def wait_for_completion(
        self,
        flow_run_id: str,
        poll_interval: int = 5,
        timeout: int = 3600
    ) -> FlowRunResult:
        """
        Wait for a flow run to complete.
        
        Args:
            flow_run_id: UUID of the flow run
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            
        Returns:
            FlowRunResult with final run information
            
        Raises:
            TimeoutError: If timeout is exceeded
        """
        start_time = datetime.now()
        
        while True:
            result = await self.get_flow_run(flow_run_id)
            
            # Check terminal states
            terminal_states = ["COMPLETED", "FAILED", "CANCELLED", "CRASHED"]
            if result.state_type in terminal_states:
                return result
            
            # Check timeout
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(
                    f"Flow run {flow_run_id} did not complete within {timeout} seconds"
                )
            
            await asyncio.sleep(poll_interval)
    
    def wait_for_completion_sync(self, flow_run_id: str, **kwargs) -> FlowRunResult:
        """Synchronous wrapper for wait_for_completion."""
        return asyncio.run(self.wait_for_completion(flow_run_id, **kwargs))
    
    async def cancel_flow_run(self, flow_run_id: str) -> bool:
        """
        Cancel a running flow.
        
        Args:
            flow_run_id: UUID of the flow run
            
        Returns:
            True if cancellation was requested successfully
        """
        async with get_client() as client:
            from prefect.client.schemas.objects import StateType
            from prefect.states import Cancelled
            
            await client.set_flow_run_state(
                flow_run_id=flow_run_id,
                state=Cancelled(),
                force=True
            )
            return True
    
    def cancel_flow_run_sync(self, flow_run_id: str) -> bool:
        """Synchronous wrapper for cancel_flow_run."""
        return asyncio.run(self.cancel_flow_run(flow_run_id))
    
    # =========================================================================
    # VARIABLE MANAGEMENT
    # =========================================================================
    
    def set_variable(
        self,
        name: str,
        value: str,
        overwrite: bool = True
    ) -> None:
        """
        Set a Prefect variable.
        
        Args:
            name: Variable name
            value: Variable value (will be stored as string)
            overwrite: If True, overwrite existing variable
        """
        Variable.set(name, value, overwrite=overwrite)
    
    def get_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a Prefect variable value.
        
        Args:
            name: Variable name
            default: Default value if variable doesn't exist
            
        Returns:
            Variable value or default
        """
        return Variable.get(name, default=default)
    
    def delete_variable(self, name: str) -> None:
        """Delete a Prefect variable."""
        Variable.unset(name)
    
    # =========================================================================
    # BLOCK MANAGEMENT
    # =========================================================================
    
    def create_secret_block(
        self,
        name: str,
        value: str,
        overwrite: bool = True
    ) -> None:
        """
        Create a Secret block.
        
        Args:
            name: Block name
            value: Secret value
            overwrite: If True, overwrite existing block
        """
        secret = Secret(value=value)
        secret.save(name, overwrite=overwrite)
    
    def get_secret_block(self, name: str) -> str:
        """
        Get value from a Secret block.
        
        Args:
            name: Block name
            
        Returns:
            Secret value
        """
        secret = Secret.load(name)
        return secret.get()
    
    async def list_blocks(self) -> List[Dict[str, Any]]:
        """
        List all blocks.
        
        Returns:
            List of block information dictionaries
        """
        async with get_client() as client:
            blocks = await client.read_block_documents()
            
            return [
                {
                    "id": str(b.id),
                    "name": b.name,
                    "type": b.block_type.slug if b.block_type else "unknown",
                    "created": str(b.created) if b.created else None
                }
                for b in blocks
            ]
    
    def list_blocks_sync(self) -> List[Dict[str, Any]]:
        """Synchronous wrapper for list_blocks."""
        return asyncio.run(self.list_blocks())
    
    # =========================================================================
    # ARTIFACT MANAGEMENT
    # =========================================================================
    
    async def create_artifact(
        self,
        key: str,
        data: Union[Dict, str],
        description: Optional[str] = None,
        kind: str = "markdown"
    ) -> str:
        """
        Create an artifact.
        
        Args:
            key: Artifact key
            data: Artifact data (markdown string or dict)
            description: Optional description
            kind: Artifact type (default: markdown)
            
        Returns:
            Artifact key
        """
        async with get_client() as client:
            await client.create_artifact(
                key=key,
                type=kind,
                data=data,
                description=description
            )
            return key

    def create_artifact_sync(self, **kwargs) -> str:
        """Synchronous wrapper for create_artifact."""
        return asyncio.run(self.create_artifact(**kwargs))

    async def read_artifacts(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Read latest artifacts.
        
        Args:
            limit: Max number of artifacts
            
        Returns:
            List of artifact info
        """
        async with get_client() as client:
            artifacts = await client.read_latest_artifacts(limit=limit)
            return [
                {
                    "id": str(a.id),
                    "key": a.key,
                    "type": a.type,
                    "data": a.data,
                    "created": str(a.created)
                }
                for a in artifacts
            ]

    def read_artifacts_sync(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous wrapper for read_artifacts."""
        return asyncio.run(self.read_artifacts(**kwargs))

    # =========================================================================
    # WEBHOOK MANAGEMENT (Cloud Only)
    # =========================================================================
    
    async def create_webhook(
        self,
        name: str,
        template: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a Cloud Webhook.
        
        Args:
            name: Webhook name
            template: Jinja2 template string
            description: Optional description
            
        Returns:
            Created webhook dict with 'endpoint' (URL)
        """
        async with get_client() as client:
            # Use raw client for Cloud-specific endpoints
            try:
                response = await client._client.post(
                    "/webhooks/",
                    json={
                        "name": name,
                        "description": description,
                        "template": template,
                        "enabled": True
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if "403" in str(e) or "Forbidden" in str(e):
                    print("Warning: Webhooks not enabled (Requires Starter Plan or higher).")
                    return {"name": name, "status": "skipped", "error": "Plan limitation"}
                raise e

    def create_webhook_sync(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for create_webhook."""
        return asyncio.run(self.create_webhook(**kwargs))

    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List Cloud Webhooks.
        
        Returns:
            List of webhook dicts
        """
        async with get_client() as client:
            response = await client._client.post("/webhooks/filter", json={})
            response.raise_for_status()
            return response.json()

    def list_webhooks_sync(self) -> List[Dict[str, Any]]:
        """Synchronous wrapper for list_webhooks."""
        return asyncio.run(self.list_webhooks())

    # =========================================================================
    # AUTOMATION MANAGEMENT
    # =========================================================================

    async def list_automations(self) -> List[Dict[str, Any]]:
        """
        List all automations.
        
        Returns:
            List of automation dictionaries
        """
        async with get_client() as client:
            # Note: read_automations might not be directly available in all client versions
            # We use the generic read_automations if available, or fall back to API
            try:
                if hasattr(client, "read_automations"):
                    automations = await client.read_automations()
                else:
                    # Fallback or specific implementation depending on SDK version
                    # For now, assuming standard client has it or we catch AttributeError
                    automations = await client.read_automations()
                
                return [
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "description": a.description,
                        "enabled": a.enabled,
                        "trigger_type": a.trigger.type if a.trigger else "unknown",
                        "actions": [act.type for act in a.actions]
                    }
                    for a in automations
                ]
            except Exception as e:
                print(f"Error listing automations: {e}")
                return []

    def list_automations_sync(self) -> List[Dict[str, Any]]:
        """Synchronous wrapper for list_automations."""
        return asyncio.run(self.list_automations())

    async def create_automation_deployment_trigger(
        self,
        name: str,
        deployment_id: str,
        match_resource_id: str = "prefect.resource.id:*",
        expect_event: str = "external.trigger"
    ) -> str:
        """
        Create an automation that triggers a deployment based on an event.
        
        Args:
            name: Automation name
            deployment_id: UUID of the deployment to trigger
            match_resource_id: Resource ID pattern to match (default: wildcard)
            expect_event: Event name to expect
            
        Returns:
            Created Automation ID
        """
        async with get_client() as client:
            # Define trigger
            trigger = EventTrigger(
                expect={expect_event},
                match={"prefect.resource.id": match_resource_id},
                posture=Posture.Reactive,
                threshold=1,
                within=0,
            )
            
            # Define action
            action = RunDeploymentAction(
                source="selected",
                deployment_id=deployment_id,
                parameters={}
            )
            
            # Create automation
            automation = AutomationCore(
                name=name,
                trigger=trigger,
                actions=[action],
                enabled=True
            )
            
            # create_automation usually returns the ID (UUID) in newer clients
            result = await client.create_automation(automation)
            return str(result)

    def create_automation_deployment_trigger_sync(self, **kwargs) -> str:
        """Synchronous wrapper for create_automation_deployment_trigger."""
        return asyncio.run(self.create_automation_deployment_trigger(**kwargs))

    async def delete_automation(self, automation_id: str) -> bool:
        """
        Delete an automation.
        
        Args:
            automation_id: UUID of the automation
            
        Returns:
            True if successful
        """
        async with get_client() as client:
            await client.delete_automation(automation_id)
            return True

    def delete_automation_sync(self, automation_id: str) -> bool:
        """Synchronous wrapper for delete_automation."""
        return asyncio.run(self.delete_automation(automation_id))

    async def pause_automation(self, automation_id: str) -> None:
        """Pause an automation."""
        async with get_client() as client:
            await client.pause_automation(automation_id)

    def pause_automation_sync(self, automation_id: str) -> None:
        """Synchronous wrapper for pause_automation."""
        return asyncio.run(self.pause_automation(automation_id))

    async def resume_automation(self, automation_id: str) -> None:
        """Resume an automation."""
        async with get_client() as client:
            await client.resume_automation(automation_id)

    def resume_automation_sync(self, automation_id: str) -> None:
        """Synchronous wrapper for resume_automation."""
        return asyncio.run(self.resume_automation(automation_id))

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Prefect Cloud connection health.
        
        Returns:
            Dictionary with connection status
        """
        try:
            async with get_client() as client:
                await client.api_healthcheck()
                
                return {
                    "status": "healthy",
                    "api_url": os.environ.get("PREFECT_API_URL", "not set"),
                    "cloud_url": self.cloud_url,
                    "account_id": self._account_id,
                    "workspace_id": self._workspace_id
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def health_check_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for health_check."""
        return asyncio.run(self.health_check())
    
    def get_dashboard_urls(self) -> Dict[str, str]:
        """
        Get useful Prefect Cloud dashboard URLs.
        
        Returns:
            Dictionary of named URLs
        """
        base = self.cloud_url
        return {
            "dashboard": base,
            "deployments": f"{base}/deployments",
            "flow_runs": f"{base}/runs",
            "blocks": f"{base}/blocks/catalog",
            "variables": f"{base}/variables",
            "automations": f"{base}/automations"
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_trigger(deployment_name: str, parameters: Optional[Dict] = None) -> FlowRunResult:
    """
    Quick function to trigger a deployment.
    
    Example:
        result = quick_trigger("My Flow/my-deployment", {"param": "value"})
        print(f"Run URL: {result.url}")
    """
    manager = PrefectManager()
    return manager.trigger_deployment_sync(deployment_name, parameters=parameters)


def quick_status(flow_run_id: str) -> FlowRunResult:
    """
    Quick function to get flow run status.
    
    Example:
        result = quick_status("abc-123-xyz")
        print(f"State: {result.state}")
    """
    manager = PrefectManager()
    return manager.get_flow_run_sync(flow_run_id)


def list_recent_runs(limit: int = 10) -> List[FlowRunResult]:
    """
    Quick function to list recent flow runs.
    
    Example:
        for run in list_recent_runs():
            print(f"{run.name}: {run.state}")
    """
    manager = PrefectManager()
    return manager.list_flow_runs_sync(limit=limit)


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    manager = PrefectManager()
    
    if len(sys.argv) < 2:
        print("Usage: python prefect_manager.py <command> [args...]")
        print("")
        print("Commands:")
        print("  health          - Check Prefect Cloud connection")
        print("  deployments     - List all deployments")
        print("  runs [limit]    - List recent flow runs")
        print("  trigger <name>  - Trigger a deployment")
        print("  status <id>     - Get flow run status")
        print("  urls            - Show dashboard URLs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health":
        result = manager.health_check_sync()
        print(f"Status: {result['status']}")
        if result['status'] == 'healthy':
            print(f"API URL: {result['api_url']}")
            print(f"Dashboard: {result['cloud_url']}")
        else:
            print(f"Error: {result.get('error', 'Unknown')}")
    
    elif command == "deployments":
        deps = manager.list_deployments_sync()
        print(f"Found {len(deps)} deployments:\n")
        for d in deps:
            print(f"  {d.flow_name}/{d.name}")
            print(f"    Tags: {', '.join(d.tags) if d.tags else 'none'}")
            print(f"    URL: {d.url}")
            print()
    
    elif command == "runs":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        runs = manager.list_flow_runs_sync(limit=limit)
        print(f"Recent {len(runs)} flow runs:\n")
        for r in runs:
            print(f"  {r.name}: {r.state}")
            print(f"    ID: {r.id}")
            print(f"    URL: {r.url}")
            print()
    
    elif command == "trigger":
        if len(sys.argv) < 3:
            print("Usage: python prefect_manager.py trigger <deployment-name>")
            sys.exit(1)
        dep_name = sys.argv[2]
        result = manager.trigger_deployment_sync(dep_name)
        print(f"Triggered: {result.name}")
        print(f"State: {result.state}")
        print(f"URL: {result.url}")
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: python prefect_manager.py status <flow-run-id>")
            sys.exit(1)
        run_id = sys.argv[2]
        result = manager.get_flow_run_sync(run_id)
        print(f"Name: {result.name}")
        print(f"State: {result.state} ({result.state_type})")
        print(f"Start: {result.start_time}")
        print(f"End: {result.end_time}")
        print(f"URL: {result.url}")
    
    elif command == "urls":
        urls = manager.get_dashboard_urls()
        print("Prefect Cloud URLs:\n")
        for name, url in urls.items():
            print(f"  {name}: {url}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
