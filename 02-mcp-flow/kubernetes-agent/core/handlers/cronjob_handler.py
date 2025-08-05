from kubernetes import client
from typing import Dict
from ..utils.logging import setup_logger, log_operation

logger = setup_logger("k8s_cronjob_handler")


class CronJobHandler:
    def __init__(self, api_client: client.ApiClient):
        self.batch_v1 = client.BatchV1Api(api_client)
        self.core_v1 = client.CoreV1Api(api_client)

    @log_operation(logger, "list_cronjobs")
    async def list_cronjobs(self, namespace: str = "default") -> Dict:
        """List all CronJobs in a namespace"""
        try:
            cronjobs = self.batch_v1.list_namespaced_cron_job(namespace)
            return {
                "status": "success",
                "data": [
                    {
                        "name": job.metadata.name,
                        "schedule": job.spec.schedule,
                        "suspend": job.spec.suspend,
                        "active": len(job.status.active) if job.status.active else 0,
                        "last_schedule": job.status.last_schedule_time.isoformat()
                        if job.status.last_schedule_time
                        else None,
                        "last_successful": job.status.last_successful_time.isoformat()
                        if job.status.last_successful_time
                        else None,
                    }
                    for job in cronjobs.items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to list CronJobs: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "describe_cronjob")
    async def describe_cronjob(self, name: str, namespace: str = "default") -> Dict:
        """Get detailed information about a CronJob"""
        try:
            cronjob = self.batch_v1.read_namespaced_cron_job(name, namespace)
            return {
                "status": "success",
                "data": {
                    "name": cronjob.metadata.name,
                    "schedule": cronjob.spec.schedule,
                    "suspend": cronjob.spec.suspend,
                    "concurrency_policy": cronjob.spec.concurrency_policy,
                    "successful_jobs_history_limit": cronjob.spec.successful_jobs_history_limit,
                    "failed_jobs_history_limit": cronjob.spec.failed_jobs_history_limit,
                    "job_template": {
                        "metadata": cronjob.spec.job_template.metadata.to_dict(),
                        "spec": {
                            "parallelism": cronjob.spec.job_template.spec.parallelism,
                            "completions": cronjob.spec.job_template.spec.completions,
                            "active_deadline_seconds": cronjob.spec.job_template.spec.active_deadline_seconds,
                            "backoff_limit": cronjob.spec.job_template.spec.backoff_limit,
                            "containers": [
                                {
                                    "name": container.name,
                                    "image": container.image,
                                    "command": container.command,
                                    "args": container.args,
                                    "resources": container.resources.to_dict()
                                    if container.resources
                                    else None,
                                }
                                for container in cronjob.spec.job_template.spec.template.spec.containers
                            ],
                        },
                    },
                    "status": {
                        "active": [
                            {
                                "name": ref.name,
                                "namespace": ref.namespace,
                                "uid": ref.uid,
                            }
                            for ref in (cronjob.status.active or [])
                        ],
                        "last_schedule_time": cronjob.status.last_schedule_time.isoformat()
                        if cronjob.status.last_schedule_time
                        else None,
                        "last_successful_time": cronjob.status.last_successful_time.isoformat()
                        if cronjob.status.last_successful_time
                        else None,
                    },
                },
            }
        except Exception as e:
            logger.error(f"Failed to describe CronJob: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "get_cronjob_logs")
    async def get_cronjob_logs(
        self,
        name: str,
        namespace: str = "default",
        container: str = None,
        tail_lines: int = None,
    ) -> Dict:
        """Get logs from the most recent job created by this CronJob"""
        try:
            # Get the CronJob to find its job template labels
            cronjob = self.batch_v1.read_namespaced_cron_job(name, namespace)
            job_labels = cronjob.spec.job_template.metadata.labels or {}

            # Find pods with matching labels
            label_selector = ",".join([f"{k}={v}" for k, v in job_labels.items()])
            pods = self.core_v1.list_namespaced_pod(
                namespace, label_selector=label_selector
            )

            # Sort pods by creation time to get the most recent ones
            sorted_pods = sorted(
                pods.items, key=lambda x: x.metadata.creation_timestamp, reverse=True
            )

            logs = {}
            for pod in sorted_pods[:5]:  # Get logs from 5 most recent pods
                try:
                    logs[pod.metadata.name] = {
                        "creation_time": pod.metadata.creation_timestamp.isoformat(),
                        "status": pod.status.phase,
                        "logs": self.core_v1.read_namespaced_pod_log(
                            pod.metadata.name,
                            namespace,
                            container=container,
                            tail_lines=tail_lines,
                        ),
                    }
                except Exception as pod_error:
                    logs[pod.metadata.name] = {
                        "creation_time": pod.metadata.creation_timestamp.isoformat(),
                        "status": pod.status.phase,
                        "error": str(pod_error),
                    }

            return {"status": "success", "data": logs}
        except Exception as e:
            logger.error(f"Failed to get CronJob logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    @log_operation(logger, "top_cronjob")
    async def top_cronjob(self, name: str, namespace: str = "default") -> Dict:
        """Get resource usage metrics for the most recent job pods"""
        try:
            # Get the CronJob to find its job template labels
            cronjob = self.batch_v1.read_namespaced_cron_job(name, namespace)
            job_labels = cronjob.spec.job_template.metadata.labels or {}

            # Find pods with matching labels
            label_selector = ",".join([f"{k}={v}" for k, v in job_labels.items()])
            pods = self.core_v1.list_namespaced_pod(
                namespace, label_selector=label_selector
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
                        {
                            "pod": pod.metadata.name,
                            "creation_time": pod.metadata.creation_timestamp.isoformat(),
                            "status": pod.status.phase,
                            "containers": container_metrics,
                        }
                    )
                except Exception as pod_error:
                    metrics.append(
                        {
                            "pod": pod.metadata.name,
                            "creation_time": pod.metadata.creation_timestamp.isoformat(),
                            "status": pod.status.phase,
                            "error": str(pod_error),
                        }
                    )

            return {"status": "success", "data": metrics}
        except Exception as e:
            logger.error(f"Failed to get CronJob metrics: {str(e)}")
            return {"status": "error", "message": str(e)}
