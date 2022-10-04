from typing import List, Optional, Dict

import yaml
from armada_client.armada.submit_pb2 import IngressConfig, ServiceConfig
from armada_jupyter.podspec import create_podspec_object, PodSpec
from armada_jupyter.constants import YMLSTR


class Job:
    """
    Represents a job to be submitted to Armada.
    """

    def __init__(
        self,
        podspec: PodSpec,
        priority: int,
        namespace: str,
        ingress: List[IngressConfig],
        services: List[ServiceConfig],
        labels: Dict[str, str],
        annotations: Dict[str, str],
    ):
        self.podspec = podspec
        self.priority = priority
        self.namespace = namespace
        self.ingress = ingress
        self.services = services
        self.labels = labels
        self.annotations = annotations

    def __repr__(self) -> str:
        return (
            f"Jobs({self.podspec}, {self.priority}, {self.namespace}, "
            f"{self.ingress}, {self.services})"
        )


class Submission:
    """
    Represents a Armada-Jupyter Submission
    """

    def __init__(self, queue: str, job_set_id: str, timeout: str, jobs: List[Job]):
        self.queue = queue
        self.job_set_id = job_set_id
        self.timeout = self.timeout_conversion(timeout)
        self.jobs = jobs

    @staticmethod
    def timeout_conversion(timeout: str) -> Optional[str]:
        """
        Convert timeout from minutes and hours into seconds.

        timeout can be in the form of 10m or 5h for example

        should return a string like 100s
        """

        if timeout[-1] == "m":
            return str(int(timeout[:-1]) * 60) + "s"
        elif timeout[-1] == "h":
            return str(int(timeout[:-1]) * 60 * 60) + "s"
        elif timeout[-1] == "s":
            return timeout

        raise ValueError("Timeout must be in the form of [x]h, [x]m or [x]s")

    def __repr__(self) -> str:
        return (
            f"Submission(queue={self.queue}, job_set_id={self.job_set_id}, "
            f"timeout={self.timeout}, jobs={self.jobs})"
        )


def convert_to_submission(file: str) -> Submission:
    """
    Converts a yaml file into a Submission object
    """

    with open(file, "r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)

    jobs = []

    for job in data["jobs"]:
        podspec = job.get(YMLSTR.PODSPEC)
        priority = job.get(YMLSTR.PRIORITY)
        namespace = job.get(YMLSTR.NAMESPACE)
        ingress = job.get(YMLSTR.INGRESS)
        services = job.get(YMLSTR.SERVICES)
        labels = job.get(YMLSTR.LABELS)
        annotations = job.get(YMLSTR.ANNOTATIONS)

        podspec = create_podspec_object(podspec)

        ingress_configs = []

        if ingress is not None:
            for i_config in ingress:
                # change key names to match protobuf
                remap_ingress_protobuf_keys(i_config)

                ingress_configs.append(IngressConfig(**i_config))

        service_configs = []

        if services is not None:
            for s_config in services:
                service_configs.append(ServiceConfig(**s_config))

        jobs.append(
            Job(
                podspec,
                priority,
                namespace,
                ingress_configs,
                service_configs,
                labels,
                annotations,
            )
        )

    return Submission(
        data[YMLSTR.QUEUE], data[YMLSTR.JOB_SET_ID], data[YMLSTR.TIMEOUT], jobs
    )


def remap_ingress_protobuf_keys(config: Dict[str, str]):
    """
    Remap keys in ingress config to match protobuf
    """

    if "tlsEnabled" in config:
        config["tls_enabled"] = config.pop("tlsEnabled")

    if "UseClusterIP" in config:
        config["use_clusterIP"] = config.pop("UseClusterIP")
