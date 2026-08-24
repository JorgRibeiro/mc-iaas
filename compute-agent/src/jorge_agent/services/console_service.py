import libvirt


LIBVIRT_URI = "qemu:///system"


class InstanceConsole:
    def __init__(self, name: str):
        self.name = name
        self.conn = None
        self.domain = None
        self.stream = None

    def open(self) -> None:
        self.conn = libvirt.open(LIBVIRT_URI)

        if self.conn is None:
            raise RuntimeError(
                "Could not connect to libvirt"
            )

        self.domain = None

        for candidate in self.conn.listAllDomains():
            if candidate.name() == self.name:
                self.domain = candidate
                break

        if self.domain is None:
            self.close()

            raise FileNotFoundError(
                f"Instance not found: {self.name}"
            )

        if not self.domain.isActive():
            self.close()

            raise RuntimeError(
                f"Instance is not running: {self.name}"
            )

        self.stream = self.conn.newStream(0)

        try:
            self.domain.openConsole(
                None,
                self.stream,
                libvirt.VIR_DOMAIN_CONSOLE_FORCE,
            )

        except Exception:
            self.close()
            raise

    def read(self, size: int = 4096) -> bytes:
        if self.stream is None:
            raise RuntimeError(
                "Console is not open"
            )

        return self.stream.recv(size)

    def write(self, data: bytes) -> int:
        if self.stream is None:
            raise RuntimeError(
                "Console is not open"
            )

        return self.stream.send(data)

    def close(self) -> None:
        if self.stream is not None:
            try:
                self.stream.finish()
            except Exception:
                try:
                    self.stream.abort()
                except Exception:
                    pass

            self.stream = None

        if self.conn is not None:
            self.conn.close()
            self.conn = None

        self.domain = None
