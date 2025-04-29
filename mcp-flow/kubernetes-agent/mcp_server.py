from mcp.server.fastmcp import FastMCP
from core.k8s_api import KubernetesAPI
from core.utils.logging import setup_logger

logger = setup_logger("k8s_mcp_server")


class KubernetesMCPServer:
    def __init__(self):
        self.mcp = FastMCP("KubernetesServer")
        self.k8s_api = KubernetesAPI()
        self._register_tools()

    def _register_tools(self):
        """Register all Kubernetes tools with MCP server"""

        # Deployment operations
        @self.mcp.tool(
            name="list_deployments", description="List all deployments in a namespace"
        )
        async def list_deployments(namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "list_deployments", {"namespace": namespace}
            )

        @self.mcp.tool(
            name="describe_deployment",
            description="Get detailed information about a deployment",
        )
        async def describe_deployment(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "describe_deployment", {"name": name, "namespace": namespace}
            )

        @self.mcp.tool(
            name="get_deployment_logs",
            description="Get logs from all pods in a deployment",
        )
        async def get_deployment_logs(
            name: str, namespace: str = "default", container: str = None
        ):
            return await self.k8s_api.handle_request(
                "get_deployment_logs",
                {"name": name, "namespace": namespace, "container": container},
            )

        @self.mcp.tool(
            name="top_deployment",
            description="Get resource usage metrics for a deployment",
        )
        async def top_deployment(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "top_deployment", {"name": name, "namespace": namespace}
            )

        # HPA operations
        @self.mcp.tool(name="list_hpas", description="List all HPAs in a namespace")
        async def list_hpas(namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "list_hpas", {"namespace": namespace}
            )

        @self.mcp.tool(
            name="describe_hpa", description="Get detailed information about an HPA"
        )
        async def describe_hpa(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "describe_hpa", {"name": name, "namespace": namespace}
            )

        @self.mcp.tool(name="top_hpa", description="Get current metrics for an HPA")
        async def top_hpa(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "top_hpa", {"name": name, "namespace": namespace}
            )

        # CronJob operations
        @self.mcp.tool(
            name="list_cronjobs", description="List all CronJobs in a namespace"
        )
        async def list_cronjobs(namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "list_cronjobs", {"namespace": namespace}
            )

        @self.mcp.tool(
            name="describe_cronjob",
            description="Get detailed information about a CronJob",
        )
        async def describe_cronjob(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "describe_cronjob", {"name": name, "namespace": namespace}
            )

        @self.mcp.tool(
            name="get_cronjob_logs", description="Get logs from the most recent job"
        )
        async def get_cronjob_logs(
            name: str, namespace: str = "default", container: str = None
        ):
            return await self.k8s_api.handle_request(
                "get_cronjob_logs",
                {"name": name, "namespace": namespace, "container": container},
            )

        @self.mcp.tool(
            name="top_cronjob",
            description="Get resource usage metrics for the most recent job pods",
        )
        async def top_cronjob(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "top_cronjob", {"name": name, "namespace": namespace}
            )

        # Service operations
        @self.mcp.tool(
            name="list_services", description="List all Services in a namespace"
        )
        async def list_services(namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "list_services", {"namespace": namespace}
            )

        @self.mcp.tool(
            name="describe_service",
            description="Get detailed information about a Service",
        )
        async def describe_service(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "describe_service", {"name": name, "namespace": namespace}
            )

        @self.mcp.tool(
            name="get_service_endpoints", description="Get endpoints for a Service"
        )
        async def get_service_endpoints(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "get_service_endpoints", {"name": name, "namespace": namespace}
            )

        # Ingress operations
        @self.mcp.tool(
            name="list_ingresses", description="List all Ingresses in a namespace"
        )
        async def list_ingresses(namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "list_ingresses", {"namespace": namespace}
            )

        @self.mcp.tool(
            name="describe_ingress",
            description="Get detailed information about an Ingress",
        )
        async def describe_ingress(name: str, namespace: str = "default"):
            return await self.k8s_api.handle_request(
                "describe_ingress", {"name": name, "namespace": namespace}
            )

        # Node operations
        @self.mcp.tool(name="list_nodes", description="List all nodes in the cluster")
        async def list_nodes():
            return await self.k8s_api.handle_request("list_nodes", {})

        @self.mcp.tool(
            name="describe_node", description="Get detailed information about a node"
        )
        async def describe_node(name: str):
            return await self.k8s_api.handle_request("describe_node", {"name": name})

        @self.mcp.tool(
            name="top_node", description="Get resource usage metrics for a node"
        )
        async def top_node(name: str):
            return await self.k8s_api.handle_request("top_node", {"name": name})

        # Cluster operations
        @self.mcp.tool(
            name="get_cluster_info", description="Get cluster-wide information"
        )
        async def get_cluster_info():
            return await self.k8s_api.handle_request("get_cluster_info", {})

    def run(self):
        """Start the MCP server"""
        try:
            logger.info("Starting Kubernetes MCP Server")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            raise
        finally:
            self.k8s_api.close()


if __name__ == "__main__":
    server = KubernetesMCPServer()
    server.run()
