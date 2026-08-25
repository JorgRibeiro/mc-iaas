from dataclasses import dataclass
from xml.sax.saxutils import escape

import libvirt

from jorge_agent.config import (
    LIBVIRT,
    STORAGE,
)


@dataclass(frozen=True)
class InstanceStorage:
    system_disk: str
    data_volume: str


def _volume_exists(pool: libvirt.virStoragePool, name: str) -> bool:
    return name in pool.listVolumes()


def create_instance_storage(name: str) -> InstanceStorage:
    if not STORAGE.base_image.exists():
        raise FileNotFoundError(
            f"Base image not found: {STORAGE.base_image}"
        )

    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    system_volume = None
    data_volume = None

    try:
        instance_pool = conn.storagePoolLookupByName(
            LIBVIRT.instance_pool
        )
        volume_pool = conn.storagePoolLookupByName(
            LIBVIRT.volume_pool
        )

        system_name = f"{name}.qcow2"
        data_name = f"{name}-data.raw"

        if _volume_exists(instance_pool, system_name):
            raise FileExistsError(
                f"System disk already exists: {system_name}"
            )

        if _volume_exists(volume_pool, data_name):
            raise FileExistsError(
                f"Data volume already exists: {data_name}"
            )

        system_xml = f"""
        <volume>
          <name>{escape(system_name)}</name>
          <capacity unit="bytes">{STORAGE.system_disk_bytes}</capacity>
          <target>
            <format type="qcow2"/>
          </target>
          <backingStore>
            <path>{escape(str(STORAGE.base_image))}</path>
            <format type="qcow2"/>
          </backingStore>
        </volume>
        """

        system_volume = instance_pool.createXML(
            system_xml,
            0,
        )

        data_xml = f"""
        <volume>
          <name>{escape(data_name)}</name>
          <capacity unit="bytes">{STORAGE.data_disk_bytes}</capacity>
          <allocation unit="bytes">0</allocation>
          <target>
            <format type="raw"/>
          </target>
        </volume>
        """

        data_volume = volume_pool.createXML(
            data_xml,
            0,
        )

        return InstanceStorage(
            system_disk=system_volume.path(),
            data_volume=data_volume.path(),
        )

    except Exception:
        # Rollback: não deixa storage pela metade.
        if data_volume is not None:
            data_volume.delete(0)

        if system_volume is not None:
            system_volume.delete(0)

        raise

    finally:
        conn.close()


def delete_instance_storage(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    try:
        instance_pool = conn.storagePoolLookupByName(
            LIBVIRT.instance_pool
        )
        volume_pool = conn.storagePoolLookupByName(
            LIBVIRT.volume_pool
        )

        system_name = f"{name}.qcow2"
        data_name = f"{name}-data.raw"

        if _volume_exists(volume_pool, data_name):
            volume_pool.storageVolLookupByName(
                data_name
            ).delete(0)

        if _volume_exists(instance_pool, system_name):
            instance_pool.storageVolLookupByName(
                system_name
            ).delete(0)

    finally:
        conn.close()


def delete_system_disk(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        pool = conn.storagePoolLookupByName(
            LIBVIRT.instance_pool
        )

        system_name = f"{name}.qcow2"

        if _volume_exists(pool, system_name):
            pool.storageVolLookupByName(
                system_name
            ).delete(0)

    finally:
        conn.close()


def delete_data_volume(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        pool = conn.storagePoolLookupByName(
            LIBVIRT.volume_pool
        )

        data_name = f"{name}-data.raw"

        if _volume_exists(pool, data_name):
            pool.storageVolLookupByName(
                data_name
            ).delete(0)

    finally:
        conn.close()


def data_volume_path(name: str) -> str | None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        pool = conn.storagePoolLookupByName(
            LIBVIRT.volume_pool
        )

        data_name = f"{name}-data.raw"

        if not _volume_exists(pool, data_name):
            return None

        return pool.storageVolLookupByName(
            data_name
        ).path()

    finally:
        conn.close()
