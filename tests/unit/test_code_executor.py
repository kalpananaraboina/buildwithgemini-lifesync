"""Unit tests for Agent Platform Sandbox Code Execution."""

import json
from pathlib import Path
from unittest.mock import patch

from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from app.agent import root_agent, _init_sandbox_code_executor


def test_root_agent_has_sandbox_code_executor():
    """Verify that root_agent has an AgentEngineSandboxCodeExecutor attached."""
    assert root_agent.code_executor is not None
    assert isinstance(root_agent.code_executor, AgentEngineSandboxCodeExecutor)
    assert root_agent.code_executor.sandbox_resource_name is not None
    assert "sandboxEnvironments" in root_agent.code_executor.sandbox_resource_name


def test_init_sandbox_code_executor_from_metadata(tmp_path):
    """Verify that _init_sandbox_code_executor reads sandbox_resource_name from deployment_metadata.json."""
    fake_metadata = {
        "remote_agent_runtime_id": "projects/123/locations/us-central1/reasoningEngines/456",
        "sandbox_resource_name": "projects/123/locations/us-central1/reasoningEngines/456/sandboxEnvironments/789",
    }
    meta_file = tmp_path / "deployment_metadata.json"
    meta_file.write_text(json.dumps(fake_metadata), encoding="utf-8")

    with patch("app.agent.Path") as mock_path:
        mock_path.return_value.resolve.return_value.parent.parent.__truediv__.return_value = meta_file
        executor = _init_sandbox_code_executor()
        assert executor is not None
        assert isinstance(executor, AgentEngineSandboxCodeExecutor)
