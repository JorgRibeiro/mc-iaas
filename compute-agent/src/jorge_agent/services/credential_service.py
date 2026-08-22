import secrets
from dataclasses import dataclass

from jorge_agent.schemas.instance import InstanceCreate


@dataclass(frozen=True)
class ResolvedCredential:
    username: str
    password: str
    generated: bool


def resolve_vm_credentials(
    instance: InstanceCreate,
) -> ResolvedCredential:
    if instance.vm_password is None:
        password = secrets.token_urlsafe(18)

        return ResolvedCredential(
            username=instance.vm_username,
            password=password,
            generated=True,
        )

    return ResolvedCredential(
        username=instance.vm_username,
        password=instance.vm_password.get_secret_value(),
        generated=False,
    )
