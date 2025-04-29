from kubernetes import client
from typing import Dict
from ..utils.logging import setup_logger, log_operation

logger = setup_logger("k8s_deployment_handler")


class DeploymentHandler:
    def __init__(self, api_client: client.ApiClient):
        self.apps_v1 = client.AppsV1Api(api_client)
        self.core_v1 = client.CoreV1Api(api_client)

    @log_operation(logger, "list_deployments")
    async def list_deployments(self, namespace: str = "default") -> Dict:
        """List all deployments in a namespace"""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return {
                "status": "success",
                "data": [
                    {
                        "name": dep.metadata.name,
                        "replicas": dep.spec.replicas,
                        "available": dep.status.available_replicas,
                        "ready": dep.status.ready_replicas,
                    }
                    for dep in deployments.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list deployments: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_deployment")
    async def describe_deployment(self, name: str, namespace: str = "default") -> Dict:
        """Get detailed information about a deployment"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
            return {
                "status": "success",
                "data": {
                    "name": deployment.metadata.name,
                    "replicas": deployment.spec.replicas,
                    "strategy": deployment.spec.strategy.type,
                    "containers": [
                        {
                            "name": container.name,
                            "image": container.image,
                            "resources": container.resources.to_dict(),
                        }
                        for container in deployment.spec.template.spec.containers
                    ],
                    "status": deployment.status.to_dict(),
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe deployment: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "get_deployment_logs")
    async def get_deployment_logs(
        self,
        name: str,
        namespace: str = "default",
        container: str = None,
        tail_lines: int = None,
    ) -> Dict:
        """Get logs from all pods in a deployment"""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace, label_selector=f"app={name}"
            )
            logs = {}
            for pod in pods.items:
                try:
                    logs[pod.metadata.name] = self.core_v1.read_namespaced_pod_log(
                        pod.metadata.name,
                        namespace,
                        container=container,
                        tail_lines=tail_lines,
                    )
                except Exception as pod_error:
                    logs[pod.metadata.name] = f"Error getting logs: {str(pod_error)}"

            return {"status": "success", "data": logs}
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "top_deployment")
    async def top_deployment(self, name: str, namespace: str = "default") -> Dict:
        """Get resource usage metrics for a deployment"""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace, label_selector=f"app={name}"
            )
            metrics = []
            for pod in pods.items:
                try:
                    pod_metrics = self.core_v1.read_namespaced_pod_status(
                        pod.metadata.name, namespace
                    )
                    container_metrics = []
                    for container_status in pod_metrics.status.container_statuses:
                        container_metrics.append(
                            {
                                "name": container_status.name,
                                "cpu": container_status.usage.cpu
                                if container_status.usage
                                else "N/A",
                                "memory": container_status.usage.memory
                                if container_status.usage
                                else "N/A",
                                "restarts": container_status.restart_count,
                                "state": next(
                                    iter(container_status.state.to_dict().keys())
                                ),
                            }
                        )
                    metrics.append(
                        {"pod": pod.metadata.name, "containers": container_metrics}
                    )
                except Exception as pod_error:
                    metrics.append({"pod": pod.metadata.name, "error": str(pod_error)})

            return {"status": "success", "data": metrics}
        except Exception as e:
            logger.error(f"Failed to get deployment metrics: {str(e)}")
            return {"status": "error", "message": str(e)}
