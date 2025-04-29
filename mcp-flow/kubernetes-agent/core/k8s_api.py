from kubernetes import client, config
from typing import Dict, Any
from .utils.logging import setup_logger
from .handlers.deployment_handler import DeploymentHandler
from .handlers.hpa_handler import HPAHandler
from .handlers.cronjob_handler import CronJobHandler
from .handlers.network_handler import NetworkHandler
from .handlers.cluster_handler import ClusterHandler

logger = setup_logger("k8s_api")


class KubernetesAPI:
    def __init__(self, config_path: str = "config.yaml"):
        try:
            # Load kubeconfig
            config.load_kube_config()
            self.api_client = client.ApiClient()

            # Initialize handlers
            self.deployment_handler = DeploymentHandler(self.api_client)
            self.hpa_handler = HPAHandler(self.api_client)
            self.cronjob_handler = CronJobHandler(self.api_client)
            self.network_handler = NetworkHandler(self.api_client)
            self.cluster_handler = ClusterHandler(self.api_client)

        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes API: {str(e)}")
            raise

    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict:
        """Handle JSON-RPC requests"""
        try:
            # Map method names to handler functions
            handlers = {
                # Deployment operations
                "list_deployments": self.deployment_handler.list_deployments,
                "describe_deployment": self.deployment_handler.describe_deployment,
                "get_deployment_logs": self.deployment_handler.get_deployment_logs,
                "top_deployment": self.deployment_handler.top_deployment,
                # HPA operations
                "list_hpas": self.hpa_handler.list_hpas,
                "describe_hpa": self.hpa_handler.describe_hpa,
                "top_hpa": self.hpa_handler.top_hpa,
                # CronJob operations
                "list_cronjobs": self.cronjob_handler.list_cronjobs,
                "describe_cronjob": self.cronjob_handler.describe_cronjob,
                "get_cronjob_logs": self.cronjob_handler.get_cronjob_logs,
                "top_cronjob": self.cronjob_handler.top_cronjob,
                # Service operations
                "list_services": self.network_handler.list_services,
                "describe_service": self.network_handler.describe_service,
                "get_service_endpoints": self.network_handler.get_service_endpoints,
                # Ingress operations
                "list_ingresses": self.network_handler.list_ingresses,
                "describe_ingress": self.network_handler.describe_ingress,
                # Node operations
                "list_nodes": self.cluster_handler.list_nodes,
                "describe_node": self.cluster_handler.describe_node,
                "top_node": self.cluster_handler.top_node,
                # Cluster operations
                "get_cluster_info": self.cluster_handler.get_cluster_info,
            }

            if method not in handlers:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                    "id": None,
                }

            # Call the appropriate handler
            result = await handlers[method](**params)

            return {"jsonrpc": "2.0", "result": result, "id": None}

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": None,
            }

    async def close(self):
        """Cleanup resources"""
        try:
            self.api_client.close()
        except Exception as e:
            logger.error(f"Error closing API client: {str(e)}")

    @staticmethod
    def format_response(result: Dict) -> Dict:
        """Format handler response into JSON-RPC format"""
        if "error" in result:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": result["error"]},
                "id": None,
            }
        else:
            return {"jsonrpc": "2.0", "result": result, "id": None}
