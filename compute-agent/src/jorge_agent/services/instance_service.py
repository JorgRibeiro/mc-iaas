from jorge_agent.schemas.instance import (
    InstanceCreate,
    InstanceCreateResponse,
    InstanceState,
    InstanceActionResponse,
)

from jorge_agent.services.cloud_init_service import (
    create_cloud_init_artifacts,
    delete_cloud_init_artifacts,
)

from jorge_agent.services.credential_service import (
    resolve_vm_credentials,
)

from jorge_agent.services.domain_service import (
    define_instance_domain,
    domain_exists,
    undefine_instance_domain,
    start_instance_domain,
    stop_instance_domain,
)

from jorge_agent.services.metadata_service import (
    metadata_exists,
    save_instance_metadata,
)

from jorge_agent.services.storage_service import (
    create_instance_storage,
    delete_instance_storage,
)

from jorge_agent.services.runtime_service import (
    prepare_instance_runtime,
    release_instance_runtime,
)

def create_instance(
    instance: InstanceCreate,
) -> InstanceCreateResponse:
    if not instance.accept_eula:
        raise ValueError(
            "Minecraft EULA must be explicitly accepted"
        )

    if domain_exists(instance.name):
        raise FileExistsError(
            f"Instance already exists: {instance.name}"
        )

    if metadata_exists(instance.name):
        raise FileExistsError(
            f"Instance metadata already exists: {instance.name}"
        )

    credential = resolve_vm_credentials(instance)

    storage_created = False
    cloud_init_created = False
    domain_defined = False

    try:
        storage = create_instance_storage(instance.name)
        storage_created = True

        cloud_init = create_cloud_init_artifacts(
            instance,
            credential,
        )
        cloud_init_created = True

        define_instance_domain(
            instance,
            storage,
            cloud_init,
        )
        domain_defined = True

        save_instance_metadata(
            instance,
            storage.data_volume,
        )

        generated_password = None

        if credential.generated:
            generated_password = credential.password

        return InstanceCreateResponse(
            name=instance.name,
            state=InstanceState.STOPPED,
            vm_username=instance.vm_username,
            memory_mb=instance.memory_mb,
            vcpus=instance.vcpus,
            minecraft_version=instance.minecraft_version,
            runtime=None,
            generated_password=generated_password,
        )

    except Exception:
        # Rollback na ordem inversa da criação.

        if domain_defined:
            undefine_instance_domain(instance.name)

        if cloud_init_created:
            delete_cloud_init_artifacts(instance.name)

        if storage_created:
            delete_instance_storage(instance.name)

        raise

def start_instance(
    name: str,
) -> InstanceActionResponse:
    if not domain_exists(name):
        raise FileNotFoundError(
            f"Instance not found: {name}"
        )

    runtime = prepare_instance_runtime(name)

    try:
        start_instance_domain(name)

        return InstanceActionResponse(
            name=name,
            state=InstanceState.RUNNING,
            runtime=runtime,
        )

    except Exception:
        # Se o boot falhar, não podemos deixar
        # IP, porta ou NIC presos.
        release_instance_runtime(name)
        raise

def stop_instance(
    name: str,
) -> InstanceActionResponse:
    if not domain_exists(name):
        raise FileNotFoundError(
            f"Instance not found: {name}"
        )

    stop_instance_domain(name)

    release_instance_runtime(name)

    return InstanceActionResponse(
        name=name,
        state=InstanceState.STOPPED,
        runtime=None,
    )