from pathlib import Path
from xml.sax.saxutils import escape

import libvirt
import time

from jorge_agent.config import LIBVIRT
from jorge_agent.schemas.instance import InstanceCreate
from jorge_agent.services.cloud_init_service import CloudInitArtifacts
from jorge_agent.services.storage_service import InstanceStorage


def _find_domain(
    conn: libvirt.virConnect,
    name: str,
) -> libvirt.virDomain | None:
    for domain in conn.listAllDomains():
        if domain.name() == name:
            return domain

    return None

def domain_exists(name: str) -> bool:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    try:
        return _find_domain(conn, name) is not None

    finally:
        conn.close()


def define_instance_domain(
    instance: InstanceCreate,
    storage: InstanceStorage,
    cloud_init: CloudInitArtifacts,
) -> None:
    system_disk = Path(storage.system_disk)
    data_volume = Path(storage.data_volume)
    seed_disk = Path(cloud_init.seed)

    for path in (
        system_disk,
        data_volume,
        seed_disk,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required disk does not exist: {path}"
            )

    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    try:
        if _find_domain(conn, instance.name) is not None:
            raise FileExistsError(
                f"Domain already exists: {instance.name}"
            )
        domain_xml = f"""
        <domain type="kvm">
          <name>{escape(instance.name)}</name>

          <memory unit="MiB">{instance.memory_mb}</memory>
          <currentMemory unit="MiB">{instance.memory_mb}</currentMemory>

          <vcpu placement="static">{instance.vcpus}</vcpu>

          <os>
            <type arch="x86_64">hvm</type>
            <boot dev="hd"/>
          </os>

          <features>
            <acpi/>
            <apic/>
          </features>

          <clock offset="utc"/>

          <on_poweroff>destroy</on_poweroff>
          <on_reboot>restart</on_reboot>
          <on_crash>restart</on_crash>

          <devices>
            <emulator>/usr/bin/qemu-system-x86_64</emulator>

            <disk type="file" device="disk">
              <driver name="qemu" type="qcow2"/>
              <source file="{escape(str(system_disk))}"/>
              <target dev="vda" bus="virtio"/>
            </disk>

            <disk type="file" device="disk">
              <driver name="qemu" type="raw"/>
              <source file="{escape(str(seed_disk))}"/>
              <target dev="vdb" bus="virtio"/>
              <readonly/>
            </disk>

            <disk type="file" device="disk">
              <driver name="qemu" type="raw"/>
              <source file="{escape(str(data_volume))}"/>
              <target dev="vdc" bus="virtio"/>
            </disk>

            <serial type="pty">
              <target type="isa-serial" port="0"/>
            </serial>

            <console type="pty">
              <target type="serial" port="0"/>
            </console>
          </devices>
        </domain>
        """

        domain = conn.defineXML(domain_xml)

        if domain is None:
            raise RuntimeError(
                f"libvirt failed to define domain: {instance.name}"
            )

    finally:
        conn.close()


def undefine_instance_domain(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError("Could not connect to libvirt")

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            return

        if domain.isActive():
            raise RuntimeError(
                f"Cannot undefine active domain: {name}"
            )

        domain.undefine()

    finally:
        conn.close()

def start_instance_domain(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if domain.isActive():
            raise RuntimeError(
                f"Instance is already active: {name}"
            )

        result = domain.create()

        if result != 0:
            raise RuntimeError(
                f"Failed to start instance: {name}"
            )

    finally:
        conn.close()

def stop_instance_domain(
    name: str,
    timeout_seconds: int = 60,
) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if not domain.isActive():
            return

        result = domain.shutdown()

        if result != 0:
            raise RuntimeError(
                f"Failed to request shutdown: {name}"
            )

        deadline = time.monotonic() + timeout_seconds

        while domain.isActive():
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Shutdown timeout for instance: {name}"
                )

            time.sleep(1)

    finally:
        conn.close()

def restart_instance_domain(name: str) -> None:
    conn = libvirt.open(LIBVIRT.uri)

    if conn is None:
        raise RuntimeError(
            "Could not connect to libvirt"
        )

    try:
        domain = _find_domain(conn, name)

        if domain is None:
            raise FileNotFoundError(
                f"Instance not found: {name}"
            )

        if not domain.isActive():
            raise RuntimeError(
                f"Instance is not running: {name}"
            )

        result = domain.reboot(0)

        if result != 0:
            raise RuntimeError(
                f"Failed to restart instance: {name}"
            )

    finally:
        conn.close()
