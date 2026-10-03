"""Trusted reverse-proxy tenant context for multi-user Web deployments."""

from __future__ import annotations

from contextvars import ContextVar, Token, copy_context
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
from typing import Callable, TypeVar


_tenant_uid: ContextVar[str | None] = ContextVar("dsa_tenant_uid", default=None)
T = TypeVar("T")


def tenant_isolation_enabled() -> bool:
    return os.getenv("TENANT_ISOLATION_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def set_tenant_uid(uid: str | None) -> Token:
    normalized = (uid or "").strip()
    return _tenant_uid.set(normalized or None)


def reset_tenant_uid(token: Token) -> None:
    _tenant_uid.reset(token)


def get_tenant_uid() -> str | None:
    return _tenant_uid.get()


def get_tenant_key() -> str:
    """Return an opaque, filesystem-safe stable key for the active user."""
    uid = get_tenant_uid()
    if not tenant_isolation_enabled() or not uid:
        return "default"
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:32]


def tenant_data_dir(base_dir: str | Path = "data") -> Path:
    return Path(base_dir) / "tenants" / get_tenant_key()


def tenant_report_dir(project_root: str | Path) -> Path:
    root = Path(project_root)
    if not tenant_isolation_enabled() or get_tenant_key() == "default":
        return root / "reports"
    return root / "reports" / "tenants" / get_tenant_key()


def bind_current_context(callback: Callable[..., T]) -> Callable[..., T]:
    """Capture ContextVars for work submitted to a thread pool."""
    context = copy_context()

    def wrapped(*args, **kwargs):
        return context.run(callback, *args, **kwargs)

    return wrapped


class TenantThreadPoolExecutor(ThreadPoolExecutor):
    """Thread pool that preserves the submitting request's tenant context."""

    def submit(self, fn, /, *args, **kwargs):
        return super().submit(bind_current_context(fn), *args, **kwargs)
