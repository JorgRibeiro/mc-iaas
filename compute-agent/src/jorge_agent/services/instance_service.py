from jorge_agent.schemas.instance import (
    InstanceCreate,
    InstanceCreateResponse,
    InstanceState,
    InstanceActionResponse,
    InstanceDeleteResponse,
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
    restart_instance_domain,
    stop_instance_domain,
    undefine_instance_domain,
)

from jorge_agent.services.metadata_service import (
    metadata_exists,
    save_instance_metadata,
    delete_instance_metadata,
    mark_instance_deleted,
)

from jorge_agent.services.storage_service import (
    create_instance_storage,
    delete_instance_storage,
    delete_system_disk,
    delete_data_volume,
    data_volume_path,
)

from jorge_agent.services.runtime_service import (
    prepare_instance_runtime,
    release_instance_runtime,
    get_instance_runtime,
)

from jorge_agent.services.secret_service import (
    create_instance_secrets,
    delete_instance_secrets,
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
    secrets_created = False

    try:
        storage = create_instance_storage(instance.name)
        storage_created = True

        secrets = create_instance_secrets(instance.name)   
        secrets_created = True

        cloud_init = create_cloud_init_artifacts(
            instance,
            credential,
            secrets.rcon_password,
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

        if secrets_created:
            delete_instance_secrets(instance.name)

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

def restart_instance(
    name: str,
) -> InstanceActionResponse:
    if not domain_exists(name):
        raise FileNotFoundError(
            f"Instance not found: {name}"
        )

    runtime = get_instance_runtime(name)

    if runtime is None:
        raise RuntimeError(
            f"Instance has no active runtime: {name}"
        )

    restart_instance_domain(name)

    return InstanceActionResponse(
        name=name,
        state=InstanceState.RUNNING,
        runtime=runtime,
    )

def delete_instance(
    name: str,
    delete_data: bool = False,
) -> InstanceDeleteResponse:
    if not domain_exists(name):
        raise FileNotFoundError(
            f"Instance not found: {name}"
        )

    # 1. Garante que a VM esteja desligada.
    stop_instance_domain(name)

    # 2. Libera qualquer runtime ainda associado.
    release_instance_runtime(name)

    # 3. Guarda o caminho antes de qualquer remoção.
    preserved_volume = data_volume_path(name)

    # 4. Remove o domínio do libvirt.
    undefine_instance_domain(name)

    # 5. Remove artefatos descartáveis.
    delete_cloud_init_artifacts(name)
    delete_instance_secrets(name)
    delete_system_disk(name)
    
    # 6. O volume persistente é tratado por último.
    if delete_data:
        delete_data_volume(name)
        delete_instance_metadata(name)

        return InstanceDeleteResponse(
            name=name,
            deleted=True,
            data_preserved=False,
            data_volume=None,
        )

    # O mundo continua existindo e guardamos metadata
    # suficiente para um futuro restore.
    mark_instance_deleted(name)

    return InstanceDeleteResponse(
        name=name,
        deleted=True,
        data_preserved=True,
        data_volume=preserved_volume,
    )