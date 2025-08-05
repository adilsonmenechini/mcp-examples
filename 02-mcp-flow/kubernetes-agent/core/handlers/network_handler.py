from kubernetes import client
from typing import Dict
from ..utils.logging import setup_logger, log_operation

logger = setup_logger("k8s_network_handler")


class NetworkHandler:
    def __init__(self, api_client: client.ApiClient):
        self.core_v1 = client.CoreV1Api(api_client)
        self.networking_v1 = client.NetworkingV1Api(api_client)

    @log_operation(logger, "list_services")
    async def list_services(self, namespace: str = "default") -> Dict:
        """List all Services in a namespace"""
        try:
            services = self.core_v1.list_namespaced_service(namespace)
            return {
                "status": "success",
                "data": [
                    {
                        "name": svc.metadata.name,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip,
                        "external_ip": svc.spec.external_i_ps[0]
                        if svc.spec.external_i_ps
                        else None,
                        "ports": [
                            {
                                "port": port.port,
                                "target_port": port.target_port,
                                "protocol": port.protocol,
                                "node_port": port.node_port
                                if svc.spec.type == "NodePort"
                                else None,
                            }
                            for port in svc.spec.ports
                        ],
                    }
                    for svc in services.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list Services: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_service")
    async def describe_service(self, name: str, namespace: str = "default") -> Dict:
        """Get detailed information about a Service"""
        try:
            service = self.core_v1.read_namespaced_service(name, namespace)
            return {
                "status": "success",
                "data": {
                    "name": service.metadata.name,
                    "namespace": service.metadata.namespace,
                    "labels": service.metadata.labels,
                    "type": service.spec.type,
                    "cluster_ip": service.spec.cluster_ip,
                    "external_ips": service.spec.external_i_ps,
                    "load_balancer_ip": service.spec.load_balancer_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "protocol": port.protocol,
                            "port": port.port,
                            "target_port": port.target_port,
                            "node_port": port.node_port
                            if service.spec.type == "NodePort"
                            else None,
                        }
                        for port in service.spec.ports
                    ],
                    "selector": service.spec.selector,
                    "session_affinity": service.spec.session_affinity,
                    "external_traffic_policy": service.spec.external_traffic_policy,
                    "health_check_node_port": service.spec.health_check_node_port,
                    "publish_not_ready_addresses": service.spec.publish_not_ready_addresses,
                    "status": {
                        "load_balancer": service.status.load_balancer.to_dict()
                        if service.status.load_balancer
                        else None
                    },
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe Service: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "list_ingresses")
    async def list_ingresses(self, namespace: str = "default") -> Dict:
        """List all Ingresses in a namespace"""
        try:
            ingresses = self.networking_v1.list_namespaced_ingress(namespace)
            return {
                "status": "success",
                "data": [
                    {
                        "name": ing.metadata.name,
                        "hosts": [rule.host for rule in ing.spec.rules],
                        "tls": [
                            {"hosts": tls.hosts, "secret_name": tls.secret_name}
                            for tls in (ing.spec.tls or [])
                        ],
                        "class": ing.spec.ingress_class_name,
                        "address": ing.status.load_balancer.ingress[0].ip
                        if ing.status.load_balancer and ing.status.load_balancer.ingress
                        else None,
                    }
                    for ing in ingresses.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list Ingresses: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_ingress")
    async def describe_ingress(self, name: str, namespace: str = "default") -> Dict:
        """Get detailed information about an Ingress"""
        try:
            ingress = self.networking_v1.read_namespaced_ingress(name, namespace)
            return {
                "status": "success",
                "data": {
                    "name": ingress.metadata.name,
                    "namespace": ingress.metadata.namespace,
                    "labels": ingress.metadata.labels,
                    "annotations": ingress.metadata.annotations,
                    "ingress_class_name": ingress.spec.ingress_class_name,
                    "rules": [
                        {
                            "host": rule.host,
                            "http": {
                                "paths": [
                                    {
                                        "path": path.path,
                                        "path_type": path.path_type,
                                        "backend": {
                                            "service": {
                                                "name": path.backend.service.name,
                                                "port": path.backend.service.port.number,
                                            }
                                            if path.backend.service
                                            else None
                                        },
                                    }
                                    for path in rule.http.paths
                                ]
                            }
                            if rule.http
                            else None,
                        }
                        for rule in ingress.spec.rules
                    ],
                    "tls": [
                        {"hosts": tls.hosts, "secret_name": tls.secret_name}
                        for tls in (ingress.spec.tls or [])
                    ],
                    "status": {
                        "load_balancer": {
                            "ingress": [
                                {"ip": ing.ip, "hostname": ing.hostname}
                                for ing in ingress.status.load_balancer.ingress
                            ]
                            if ingress.status.load_balancer
                            and ingress.status.load_balancer.ingress
                            else []
                        }
                    },
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe Ingress: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "get_service_endpoints")
    async def get_service_endpoints(
        self, name: str, namespace: str = "default"
    ) -> Dict:
        """Get endpoints for a Service"""
        try:
            endpoints = self.core_v1.read_namespaced_endpoints(name, namespace)
            return {
                "status": "success",
                "data": {
                    "name": endpoints.metadata.name,
                    "subsets": [
                        {
                            "addresses": [
                                {
                                    "ip": addr.ip,
                                    "hostname": addr.hostname,
                                    "node_name": addr.node_name,
                                    "target_ref": {
                                        "kind": addr.target_ref.kind,
                                        "name": addr.target_ref.name,
                                        "namespace": addr.target_ref.namespace,
                                    }
                                    if addr.target_ref
                                    else None,
                                }
                                for addr in subset.addresses
                            ]
                            if subset.addresses
                            else [],
                            "ports": [
                                {
                                    "name": port.name,
                                    "port": port.port,
                                    "protocol": port.protocol,
                                }
                                for port in subset.ports
                            ]
                            if subset.ports
                            else [],
                        }
                        for subset in endpoints.subsets
                    ]
                    if endpoints.subsets
                    else [],
                },
            }
        except Exception as e:
            logger.error(f"Failed to get Service endpoints: {str(e)}")
            return {"status": "error", "message": str(e)}
