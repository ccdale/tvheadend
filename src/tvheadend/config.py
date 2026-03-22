from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TVHConfig",
    "clearConfig",
    "configure",
    "getConfig",
]


@dataclass(slots=True)
class TVHConfig:
    host: str
    username: str
    password: str
    scheme: str = "http"
    port: int | None = None
    timeout: float = 10.0

    @property
    def auth(self) -> tuple[str, str]:
        return self.username, self.password

    @property
    def netloc(self) -> str:
        cleaned_host = self.host.rstrip("/")
        if self.port is None:
            return cleaned_host
        return f"{cleaned_host}:{self.port}"

    def api_url(self, route: str) -> str:
        cleaned_route = route.lstrip("/")
        return f"{self.scheme}://{self.netloc}/api/{cleaned_route}"


_config: TVHConfig | None = None


def configure(
    host: str,
    username: str,
    password: str,
    *,
    scheme: str = "http",
    port: int | None = None,
    timeout: float = 10.0,
) -> TVHConfig:
    global _config
    _config = TVHConfig(
        host=host,
        username=username,
        password=password,
        scheme=scheme,
        port=port,
        timeout=timeout,
    )
    return _config


def getConfig() -> TVHConfig:
    if _config is None:
        raise RuntimeError(
            "TVHeadend configuration is not set. Call tvheadend.configure(...) first."
        )
    return _config


def clearConfig() -> None:
    global _config
    _config = None


def get_config() -> TVHConfig:
    return getConfig()


def clear_config() -> None:
    clearConfig()
