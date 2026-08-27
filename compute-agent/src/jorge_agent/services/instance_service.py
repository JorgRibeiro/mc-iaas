import logging


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
    is_instance_active,
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

from jorge_agent.services.lock_service import (
    instance_lock,
    runtime_lock,
)

logger = logging.getLogger(__name__)

def create_instance(
    instance: InstanceCreate,
) -> InstanceCreateResponse:
    logger.info(
        "event=instance.create.requested "
        "name=%s memory_mb=%s vcpus=%s version=%s",
        instance.name,
        instance.memory_mb,
        instance.vcpus,
        instance.minecraft_version,
    )

    if not instance.accept_eula:
        logger.warning(
            "event=instance.create.rejected "
            "name=%s reason=eula_not_accepted",
            instance.name,
        )

        raise ValueError(
            "Minecraft EULA must be explicitly accepted"
        )

    with instance_lock(instance.name):
        if domain_exists(instance.name):
            logger.warning(
                "event=instance.create.rejected "
                "name=%s reason=domain_exists",
                instance.name,
            )

            raise FileExistsError(
                f"Instance already exists: {instance.name}"
            )

        if metadata_exists(instance.name):
            logger.warning(
                "event=instance.create.rejected "
                "name=%s reason=metadata_exists",
                instance.name,
            )

            raise FileExistsError(
                f"Instance metadata already exists: {instance.name}"
            )

        credential = resolve_vm_credentials(
            instance
        )

        storage_created = False
        cloud_init_created = False
        domain_defined = False
        secrets_created = False

        try:
            storage = create_instance_storage(
                instance.name
            )
            storage_created = True

            secrets = create_instance_secrets(
                instance.name
            )
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
                generated_password = (
                    credential.password
                )

            response = InstanceCreateResponse(
                name=instance.name,
                state=InstanceState.STOPPED,
                vm_username=instance.vm_username,
                memory_mb=instance.memory_mb,
                vcpus=instance.vcpus,
                minecraft_version=(
                    instance.minecraft_version
                ),
                runtime=None,
                generated_password=generated_password,
            )

            logger.info(
                "event=instance.create.completed "
                "name=%s state=stopped",
                instance.name,
            )

            return response

        except Exception as exc:
            logger.error(
                "event=instance.create.failed "
                "name=%s error_type=%s",
                instance.name,
                type(exc).__name__,
            )

            logger.warning(
                "event=instance.create.rollback "
                "name=%s",
                instance.name,
            )

            # Rollback na ordem inversa da criação.
            if domain_defined:
                undefine_instance_domain(
                    instance.name
                )

            if cloud_init_created:
                delete_cloud_init_artifacts(
                    instance.name
                )

            if storage_created:
                delete_instance_storage(
                    instance.name
                )

            if secrets_created:
                delete_instance_secrets(
                    instance.name
                )

            raise

def start_instance(
    name: str,
) -> InstanceActionResponse:
    logger.info(
        "event=instance.start.requested name=%s",
        name,
    )

    with instance_lock(name):
        if not domain_exists(name):
            logger.warning(
                "event=instance.start.rejected "
                "name=%s reason=not_found",
                name,
            )

            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        try:
            with runtime_lock():
                runtime = prepare_instance_runtime(
                    name
                )

            logger.info(
                "event=instance.start.runtime_allocated "
                "name=%s slot=%s ip=%s port=%s",
                name,
                runtime.slot,
                runtime.ip,
                runtime.external_port,
            )

        except Exception as exc:
            logger.error(
                "event=instance.start.failed "
                "name=%s stage=runtime_prepare "
                "error_type=%s",
                name,
                type(exc).__name__,
            )

            raise

        try:
            start_instance_domain(name)

        except Exception as exc:
            logger.error(
                "event=instance.start.failed "
                "name=%s stage=domain_start "
                "error_type=%s",
                name,
                type(exc).__name__,
            )

            logger.warning(
                "event=instance.start.rollback "
                "name=%s",
                name,
            )

            # Se o boot falhar, não podemos deixar
            # IP, porta ou NIC presos.
            with runtime_lock():
                release_instance_runtime(
                    name
                )

            raise

        logger.info(
            "event=instance.start.completed "
            "name=%s slot=%s ip=%s port=%s",
            name,
            runtime.slot,
            runtime.ip,
            runtime.external_port,
        )

        return InstanceActionResponse(
            name=name,
            state=InstanceState.RUNNING,
            runtime=runtime,
        )

def stop_instance(
    name: str,
) -> InstanceActionResponse:
    logger.info(
        "event=instance.stop.requested name=%s",
        name,
    )

    with instance_lock(name):
        if not domain_exists(name):
            logger.warning(
                "event=instance.stop.rejected "
                "name=%s reason=not_found",
                name,
            )

            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        try:
            stop_instance_domain(name)

            with runtime_lock():
                release_instance_runtime(
                    name
                )

        except Exception as exc:
            logger.error(
                "event=instance.stop.failed "
                "name=%s error_type=%s",
                name,
                type(exc).__name__,
            )

            raise

        logger.info(
            "event=instance.stop.completed "
            "name=%s state=stopped",
            name,
        )

        return InstanceActionResponse(
            name=name,
            state=InstanceState.STOPPED,
            runtime=None,
        )

def restart_instance(
    name: str,
) -> InstanceActionResponse:
    logger.info(
        "event=instance.restart.requested name=%s",
        name,
    )

    with instance_lock(name):
        if not domain_exists(name):
            logger.warning(
                "event=instance.restart.rejected "
                "name=%s reason=not_found",
                name,
            )

            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        runtime = get_instance_runtime(
            name
        )

        if runtime is None:
            logger.warning(
                "event=instance.restart.rejected "
                "name=%s reason=no_runtime",
                name,
            )

            raise RuntimeError(
                f"Instance has no active runtime: {name}"
            )

        try:
            restart_instance_domain(
                name
            )

        except Exception as exc:
            logger.error(
                "event=instance.restart.failed "
                "name=%s error_type=%s",
                name,
                type(exc).__name__,
            )

            raise

        logger.info(
            "event=instance.restart.completed "
            "name=%s slot=%s ip=%s port=%s",
            name,
            runtime.slot,
            runtime.ip,
            runtime.external_port,
        )

        return InstanceActionResponse(
            name=name,
            state=InstanceState.RUNNING,
            runtime=runtime,
        )

def delete_instance(
    name: str,
    delete_data: bool = False,
) -> InstanceDeleteResponse:
    logger.info(
        "event=instance.delete.requested "
        "name=%s delete_data=%s",
        name,
        delete_data,
    )

    with instance_lock(name):
        if not domain_exists(name):
            logger.warning(
                "event=instance.delete.rejected "
                "name=%s reason=not_found",
                name,
            )

            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if is_instance_active(name):
            logger.warning(
                "event=instance.delete.rejected "
                "name=%s reason=instance_active",
                name,
            )

            raise RuntimeError(
                f"Instance must be stopped before deletion: {name}"
            )

        try:
            # 1. Libera qualquer runtime residual.
            with runtime_lock():
                release_instance_runtime(
                    name
                )

            # 2. Guarda o caminho antes
            # de qualquer remoção.
            preserved_volume = (
                data_volume_path(name)
            )

            # 3. Remove o domínio do libvirt.
            undefine_instance_domain(
                name
            )

            # 4. Remove artefatos descartáveis.
            delete_cloud_init_artifacts(
                name
            )

            delete_instance_secrets(
                name
            )

            delete_system_disk(
                name
            )

            # 5. O volume persistente
            # é tratado por último.
            if delete_data:
                delete_data_volume(
                    name
                )

                delete_instance_metadata(
                    name
                )

                response = (
                    InstanceDeleteResponse(
                        name=name,
                        deleted=True,
                        data_preserved=False,
                        data_volume=None,
                    )
                )

            else:
                mark_instance_deleted(
                    name
                )

                response = (
                    InstanceDeleteResponse(
                        name=name,
                        deleted=True,
                        data_preserved=True,
                        data_volume=(
                            preserved_volume
                        ),
                    )
                )

        except Exception as exc:
            logger.error(
                "event=instance.delete.failed "
                "name=%s error_type=%s",
                name,
                type(exc).__name__,
            )

            raise

        logger.info(
            "event=instance.delete.completed "
            "name=%s data_preserved=%s",
            name,
            response.data_preserved,
        )

        return response 