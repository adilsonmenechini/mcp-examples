import pytest
import asyncio
from kubernetes import client, config
from ..core.k8s_api import KubernetesAPI
from ..core.handlers.deployment_handler import DeploymentHandler
from ..core.handlers.hpa_handler import HPAHandler
from ..core.handlers.cronjob_handler import CronJobHandler
from ..core.handlers.network_handler import NetworkHandler
from ..core.handlers.cluster_handler import ClusterHandler

@pytest.fixture
async def k8s_api():
    api = KubernetesAPI()
    yield api
    await api.close()

@pytest.mark.asyncio
async def test_list_deployments(k8s_api):
    result = await k8s_api.handle_request("list_deployments", {"namespace": "default"})
    assert result["status"] == "success"
    assert "data" in result

@pytest.mark.asyncio
async def test_list_nodes(k8s_api):
    result = await k8s_api.handle_request("list_nodes", {})
    assert result["status"] == "success"
    assert "data" in result

@pytest.mark.asyncio
async def test_get_cluster_info(k8s_api):
    result = await k8s_api.handle_request("get_cluster_info", {})
    assert result["status"] == "success"
    assert "data" in result
    assert "version" in result["data"]

@pytest.mark.asyncio
async def test_list_services(k8s_api):
    result = await k8s_api.handle_request("list_services", {"namespace": "default"})
    assert result["status"] == "success"
    assert "data" in result

@pytest.mark.asyncio
async def test_error_handling(k8s_api):
    # Test with invalid namespace
    result = await k8s_api.handle_request("list_deployments", {"namespace": "nonexistent"})
    assert result["status"] == "error"
    assert "message" in result
