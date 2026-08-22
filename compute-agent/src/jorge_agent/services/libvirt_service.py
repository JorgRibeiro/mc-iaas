import libvirt

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