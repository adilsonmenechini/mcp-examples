from kubernetes import client
from typing import Dict
from ..utils.logging import setup_logger, log_operation

logger = setup_logger("k8s_hpa_handler")


class HPAHandler:
    def __init__(self, api_client: client.ApiClient):
        self.autoscaling_v1 = client.AutoscalingV1Api(api_client)
        self.autoscaling_v2 = client.AutoscalingV2Api(api_client)

    @log_operation(logger, "list_hpas")
    async def list_hpas(self, namespace: str = "default") -> Dict:
        """List all HPAs in a namespace"""
        try:
            hpas = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
                namespace
            )
            return {
                "status": "success",
                "data": [
                    {
                        "name": hpa.metadata.name,
                        "min_replicas": hpa.spec.min_replicas,
                        "max_replicas": hpa.spec.max_replicas,
                        "current_replicas": hpa.status.current_replicas,
                        "target": {
                            "name": hpa.spec.scale_target_ref.name,
                            "kind": hpa.spec.scale_target_ref.kind,
                        },
                        "metrics": [
                            self._format_metric(metric)
                            for metric in (hpa.spec.metrics or [])
                        ],
                    }
                    for hpa in hpas.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list HPAs: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_hpa")
    async def describe_hpa(self, name: str, namespace: str = "default") -> Dict:
        """Get detailed information about an HPA"""
        try:
            hpa = self.autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(
                name, namespace
            )
            return {
                "status": "success",
                "data": {
                    "name": hpa.metadata.name,
                    "min_replicas": hpa.spec.min_replicas,
                    "max_replicas": hpa.spec.max_replicas,
                    "current_replicas": hpa.status.current_replicas,
                    "target": {
                        "name": hpa.spec.scale_target_ref.name,
                        "kind": hpa.spec.scale_target_ref.kind,
                        "api_version": hpa.spec.scale_target_ref.api_version,
                    },
                    "metrics": [
                        self._format_metric(metric)
                        for metric in (hpa.spec.metrics or [])
                    ],
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
                        for condition in (hpa.status.conditions or [])
                    ],
                    "current_metrics": [
                        self._format_current_metric(metric)
                        for metric in (hpa.status.current_metrics or [])
                    ],
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe HPA: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "top_hpa")
    async def top_hpa(self, name: str, namespace: str = "default") -> Dict:
        """Get current metrics for an HPA"""
        try:
            hpa = self.autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(
                name, namespace
            )
            return {
                "status": "success",
                "data": {
                    "name": hpa.metadata.name,
                    "current_replicas": hpa.status.current_replicas,
                    "desired_replicas": hpa.status.desired_replicas,
                    "current_metrics": [
                        self._format_current_metric(metric)
                        for metric in (hpa.status.current_metrics or [])
                    ],
                },
            }
        except Exception as e:
            logger.error(f"Failed to get HPA metrics: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _format_metric(self, metric) -> Dict:
        """Format HPA metric specification"""
        metric_data = {"type": metric.type}

        if metric.type == "Resource":
            metric_data.update(
                {
                    "name": metric.resource.name,
                    "target_type": metric.resource.target.type,
                    "target_value": (
                        metric.resource.target.average_value
                        if metric.resource.target.type == "AverageValue"
                        else metric.resource.target.average_utilization
                    ),
                }
            )
        elif metric.type == "Pods":
            metric_data.update(
                {
                    "metric": metric.pods.metric.name,
                    "target_type": metric.pods.target.type,
                    "target_value": metric.pods.target.average_value,
                }
            )
        elif metric.type == "Object":
            metric_data.update(
                {
                    "metric": metric.object.metric.name,
                    "target_type": metric.object.target.type,
                    "target_value": metric.object.target.value,
                    "described_object": {
                        "kind": metric.object.described_object.kind,
                        "name": metric.object.described_object.name,
                        "api_version": metric.object.described_object.api_version,
                    },
                }
            )

        return metric_data

    def _format_current_metric(self, metric) -> Dict:
        """Format HPA current metric status"""
        metric_data = {"type": metric.type}

        if metric.type == "Resource":
            metric_data.update(
                {
                    "name": metric.resource.name,
                    "current_value": (
                        metric.resource.current.average_value
                        if hasattr(metric.resource.current, "average_value")
                        else metric.resource.current.average_utilization
                    ),
                }
            )
        elif metric.type == "Pods":
            metric_data.update(
                {
                    "metric": metric.pods.metric.name,
                    "current_value": metric.pods.current.average_value,
                }
            )
        elif metric.type == "Object":
            metric_data.update(
                {
                    "metric": metric.object.metric.name,
                    "current_value": metric.object.current.value,
                }
            )

        return metric_data
