from kubernetes import client, config
import yaml
import os
from typing import List
from kubernetes.client.rest import ApiException


class K8sAgent:
    def __init__(self, config_path: str = "config.yaml"):
        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f)
            kubeconfig_path = os.path.expanduser(cfg["kubernetes"]["kubeconfig"])
            config.load_kube_config(config_file=kubeconfig_path)
            self.v1 = client.CoreV1Api()
        except Exception as e:
            raise Exception(f"Failed to initialize K8s client: {str(e)}")

    def list_pods(self, namespace: str = "default") -> List[dict]:
        try:
            pods = self.v1.list_namespaced_pod(namespace)
            return [
                {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                }
                for pod in pods.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to list pods: {str(e)}")

    def list_nodes(self) -> List[dict]:
        try:
            nodes = self.v1.list_node()
            return [
                {
                    "name": node.metadata.name,
                    "status": node.status.conditions[-1].type,
                    "addresses": [addr.address for addr in node.status.addresses],
                }
                for node in nodes.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to list nodes: {str(e)}")

    def get_pod_logs(self, name: str, namespace: str = "default") -> str:
        try:
            return self.v1.read_namespaced_pod_log(name, namespace)
        except ApiException as e:
            raise Exception(f"Failed to get pod logs: {str(e)}")

    def close(self) -> None:
        # Cleanup resources if needed
        pass
