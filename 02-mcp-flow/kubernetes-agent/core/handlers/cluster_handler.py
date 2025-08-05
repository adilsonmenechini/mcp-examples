from kubernetes import client
from typing import Dict
from ..utils.logging import setup_logger, log_operation

logger = setup_logger("k8s_cluster_handler")


class ClusterHandler:
    def __init__(self, api_client: client.ApiClient):
        self.core_v1 = client.CoreV1Api(api_client)
        self.version_api = client.VersionApi(api_client)

    @log_operation(logger, "list_nodes")
    async def list_nodes(self) -> Dict:
        """List all nodes in the cluster"""
        try:
            nodes = self.core_v1.list_node()
            return {
                "status": "success",
                "data": [
                    {
                        "name": node.metadata.name,
                        "status": node.status.conditions[-1].type,
                        "roles": node.metadata.labels.get(
                            "kubernetes.io/role", "worker"
                        ),
                        "version": node.status.node_info.kubelet_version,
                        "internal_ip": next(
                            (
                                addr.address
                                for addr in node.status.addresses
                                if addr.type == "InternalIP"
                            ),
                            None,
                        ),
                        "external_ip": next(
                            (
                                addr.address
                                for addr in node.status.addresses
                                if addr.type == "ExternalIP"
                            ),
                            None,
                        ),
                        "os_image": node.status.node_info.os_image,
                        "container_runtime": node.status.node_info.container_runtime_version,
                        "ready": any(
                            cond.type == "Ready" and cond.status == "True"
                            for cond in node.status.conditions
                        ),
                    }
                    for node in nodes.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list nodes: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_node")
    async def describe_node(self, name: str) -> Dict:
        """Get detailed information about a node"""
        try:
            node = self.core_v1.read_node(name)
            return {
                "status": "success",
                "data": {
                    "name": node.metadata.name,
                    "labels": node.metadata.labels,
                    "annotations": node.metadata.annotations,
                    "creation_timestamp": node.metadata.creation_timestamp.isoformat(),
                    "info": {
                        "architecture": node.status.node_info.architecture,
                        "boot_id": node.status.node_info.boot_id,
                        "container_runtime": node.status.node_info.container_runtime_version,
                        "kernel_version": node.status.node_info.kernel_version,
                        "kube_proxy_version": node.status.node_info.kube_proxy_version,
                        "kubelet_version": node.status.node_info.kubelet_version,
                        "operating_system": node.status.node_info.operating_system,
                        "os_image": node.status.node_info.os_image,
                    },
                    "addresses": [
                        {"type": addr.type, "address": addr.address}
                        for addr in node.status.addresses
                    ],
                    "capacity": {
                        "cpu": node.status.capacity.get("cpu"),
                        "memory": node.status.capacity.get("memory"),
                        "pods": node.status.capacity.get("pods"),
                    },
                    "allocatable": {
                        "cpu": node.status.allocatable.get("cpu"),
                        "memory": node.status.allocatable.get("memory"),
                        "pods": node.status.allocatable.get("pods"),
                    },
                    "conditions": [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition_time": condition.last_transition_time.isoformat()
                            if condition.last_transition_time
                            else None,
                        }
                        for condition in node.status.conditions
                    ],
                    "taints": [
                        {"key": taint.key, "value": taint.value, "effect": taint.effect}
                        for taint in (node.spec.taints or [])
                    ],
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe node: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "top_node")
    async def top_node(self, name: str) -> Dict:
        """Get resource usage metrics for a node"""
        try:
            # Get node metrics
            metrics = self.core_v1.read_node_status(name)

            # Get pods running on the node
            field_selector = f"spec.nodeName={name}"
            pods = self.core_v1.list_pod_for_all_namespaces(
                field_selector=field_selector
            )

            return {
                "status": "success",
                "data": {
                    "name": name,
                    "usage": {
                        "cpu": metrics.usage.cpu if metrics.usage else "N/A",
                        "memory": metrics.usage.memory if metrics.usage else "N/A",
                    },
                    "pods": [
                        {
                            "name": pod.metadata.name,
                            "namespace": pod.metadata.namespace,
                            "status": pod.status.phase,
                            "containers": [
                                {
                                    "name": container.name,
                                    "ready": container.ready,
                                    "restarts": container.restart_count,
                                    "state": next(
                                        iter(container.state.to_dict().keys())
                                    ),
                                }
                                for container in pod.status.container_statuses
                            ]
                            if pod.status.container_statuses
                            else [],
                        }
                        for pod in pods.items
                    ],
                },
            }
        except Exception as e:
            logger.error(f"Failed to get node metrics: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "get_cluster_info")
    async def get_cluster_info(self) -> Dict:
        """Get cluster-wide information"""
        try:
            version = self.version_api.get_code()
            nodes = self.core_v1.list_node()
            namespaces = self.core_v1.list_namespace()
            pods = self.core_v1.list_pod_for_all_namespaces()

            # Calculate node metrics
            total_cpu = 0
            total_memory = 0
            allocatable_cpu = 0
            allocatable_memory = 0
            for node in nodes.items:
                if node.status.capacity:
                    total_cpu += float(node.status.capacity.get("cpu", 0))
                    total_memory += self._parse_memory(
                        node.status.capacity.get("memory", "0")
                    )
                if node.status.allocatable:
                    allocatable_cpu += float(node.status.allocatable.get("cpu", 0))
                    allocatable_memory += self._parse_memory(
                        node.status.allocatable.get("memory", "0")
                    )

            return {
                "status": "success",
                "data": {
                    "version": {
                        "major": version.major,
                        "minor": version.minor,
                        "platform": version.platform,
                        "git_version": version.git_version,
                        "build_date": version.build_date,
                    },
                    "nodes": {
                        "count": len(nodes.items),
                        "ready": sum(
                            1
                            for node in nodes.items
                            if any(
                                cond.type == "Ready" and cond.status == "True"
                                for cond in node.status.conditions
                            )
                        ),
                    },
                    "resources": {
                        "total": {"cpu": total_cpu, "memory": total_memory},
                        "allocatable": {
                            "cpu": allocatable_cpu,
                            "memory": allocatable_memory,
                        },
                    },
                    "pods": {
                        "total": len(pods.items),
                        "running": sum(
                            1 for pod in pods.items if pod.status.phase == "Running"
                        ),
                        "pending": sum(
                            1 for pod in pods.items if pod.status.phase == "Pending"
                        ),
                        "failed": sum(
                            1 for pod in pods.items if pod.status.phase == "Failed"
                        ),
                    },
                    "namespaces": {
                        "count": len(namespaces.items),
                        "names": [ns.metadata.name for ns in namespaces.items],
                    },
                },
            }
        except Exception as e:
            logger.error(f"Failed to get cluster info: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _parse_memory(self, memory_str: str) -> float:
        """Convert Kubernetes memory string to bytes"""
        try:
            if memory_str.endswith("Ki"):
                return float(memory_str[:-2]) * 1024
            elif memory_str.endswith("Mi"):
                return float(memory_str[:-2]) * 1024 * 1024
            elif memory_str.endswith("Gi"):
                return float(memory_str[:-2]) * 1024 * 1024 * 1024
            elif memory_str.endswith("Ti"):
                return float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024
            else:
                return float(memory_str)
        except (ValueError, AttributeError):
            return 0
