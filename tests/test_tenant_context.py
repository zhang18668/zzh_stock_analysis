from __future__ import annotations

from pathlib import Path

from src.tenant_context import (
    TenantThreadPoolExecutor,
    get_tenant_key,
    reset_tenant_uid,
    set_tenant_uid,
    tenant_report_dir,
)


def test_tenant_key_and_report_dir_are_stable_and_opaque(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TENANT_ISOLATION_ENABLED", "true")
    token = set_tenant_uid("authentik-user-id")
    try:
        tenant_key = get_tenant_key()
        assert tenant_key != "authentik-user-id"
        assert len(tenant_key) == 32
        assert tenant_report_dir(tmp_path) == tmp_path / "reports" / "tenants" / tenant_key
    finally:
        reset_tenant_uid(token)


def test_tenant_executor_propagates_context(monkeypatch):
    monkeypatch.setenv("TENANT_ISOLATION_ENABLED", "true")
    token = set_tenant_uid("user-a")
    try:
        expected = get_tenant_key()
        with TenantThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(get_tenant_key).result(timeout=5) == expected
    finally:
        reset_tenant_uid(token)


def test_missing_uid_uses_default_context(monkeypatch):
    monkeypatch.setenv("TENANT_ISOLATION_ENABLED", "true")
    token = set_tenant_uid(None)
    try:
        assert get_tenant_key() == "default"
    finally:
        reset_tenant_uid(token)
