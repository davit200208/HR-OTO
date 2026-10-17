import os
from dataclasses import dataclass


class SecretStoreUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SecretMetadata:
    configured: bool
    version: int
    last4: str


class SecretStore:
    def get(self, provider: str) -> str | None: raise NotImplementedError
    def put(self, provider: str, value: str, version: int) -> None: raise NotImplementedError
    def delete(self, provider: str) -> None: raise NotImplementedError


class EnvironmentSecretStore(SecretStore):
    """Deployment adapter: production should replace this with Vault/KMS.

    Secrets are read from environment variables and never persisted in the DB.
    Mutation is deliberately refused until a real secret manager is configured.
    """
    def get(self, provider: str) -> str | None:
        return os.getenv(f"HR_OTO_{provider.upper()}_API_KEY")

    def put(self, provider: str, value: str, version: int) -> None:
        raise SecretStoreUnavailable("Configure a KMS/Vault SecretStore before rotating provider secrets")

    def delete(self, provider: str) -> None:
        raise SecretStoreUnavailable("Environment secrets cannot be deleted by the API")


class InMemorySecretStore(SecretStore):
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
    def get(self, provider: str) -> str | None: return self.values.get(provider)
    def put(self, provider: str, value: str, version: int) -> None: self.values[provider] = value
    def delete(self, provider: str) -> None: self.values.pop(provider, None)


_store: SecretStore = EnvironmentSecretStore()


def get_secret_store() -> SecretStore:
    return _store


def set_secret_store_for_tests(store: SecretStore) -> None:
    global _store
    _store = store


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    return "*" * max(0, len(value) - 4) + value[-4:]
