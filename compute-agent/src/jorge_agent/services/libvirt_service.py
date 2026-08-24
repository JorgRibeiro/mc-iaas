import libvirt

from jorge_agent.schemas.instance import (
    InstanceResponse,
    InstanceState,
    RuntimeAllocation,
    InstanceDetailResponse,
)

from jorge_agent.services.metadata_service import (
    load_instance_metadata,
)

from jorge_agent.services.runtime_service import (
    get_instance_runtime,
)

LIBVIRT_URI = "qemu:///system"

def get_hypervisor_status() -> dict:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError("Não foi possível conectar ao libvirt")

    try:
        version = conn.getLibVersion()

        major = version // 1_000_000
        minor = (version // 1_000) % 1_000
        release = version % 1_000

        return {
            "uri": conn.getURI(),
            "hostname": conn.getHostname(),
            "libvirt_version": f"{major}.{minor}.{release}",
            "active_domains": conn.numOfDomains(),
            "defined_domains": conn.numOfDefinedDomains(),
        }
    finally:
        conn.close()


def map_domain_state(state: int) -> InstanceState:
    state_map = {
        libvirt.VIR_DOMAIN_RUNNING: InstanceState.RUNNING,
        libvirt.VIR_DOMAIN_BLOCKED: InstanceState.RUNNING,
        libvirt.VIR_DOMAIN_PAUSED: InstanceState.PAUSED,
        libvirt.VIR_DOMAIN_SHUTDOWN: InstanceState.STOPPING,
        libvirt.VIR_DOMAIN_SHUTOFF: InstanceState.STOPPED,
        libvirt.VIR_DOMAIN_CRASHED: InstanceState.ERROR,
        libvirt.VIR_DOMAIN_PMSUSPENDED: InstanceState.PAUSED,
    }

    return state_map.get(
        state,
        InstanceState.UNKNOWN,
    )

def list_instances() -> list[InstanceResponse]:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError("Não foi possível conectar ao libvirt")

    try:
        instances = []

        for domain in conn.listAllDomains():
            info = domain.info()

            state = map_domain_state(info[0])
            memory_mb = info[1] // 1024
            vcpus = info[3]

            instances.append(
                InstanceResponse(
                    name=domain.name(),
                    state=state,
                    memory_mb=memory_mb,
                    vcpus=vcpus,
                    runtime=None,
                )
            )

        return instances

    finally:
        conn.close()

def get_instance(name: str) -> InstanceDetailResponse:
    conn = libvirt.open(LIBVIRT_URI)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = None

        for candidate in conn.listAllDomains():
            if candidate.name() == name:
                domain = candidate
                break

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        info = domain.info()

        state = map_domain_state(info[0])
        memory_mb = info[1] // 1024
        vcpus = info[3]

        metadata = load_instance_metadata(name)
        runtime = get_instance_runtime(name)

        return InstanceDetailResponse(
            name=name,
            state=state,
            vm_username=metadata["vm_username"],
            memory_mb=memory_mb,
            vcpus=vcpus,
            minecraft_version=metadata[
                "minecraft_version"
            ],
            runtime=runtime,
        )

    finally:
        conn.close()
