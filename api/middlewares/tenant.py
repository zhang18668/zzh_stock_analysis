"""Bind the Authentik identity header to the request tenant context."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.tenant_context import reset_tenant_uid, set_tenant_uid, tenant_isolation_enabled


def add_tenant_middleware(app: FastAPI) -> None:
    if not tenant_isolation_enabled():
        return

    header_name = os.getenv("TENANT_ID_HEADER", "X-authentik-uid")

    @app.middleware("http")
    async def trusted_proxy_tenant(request: Request, call_next):
        uid = request.headers.get(header_name, "").strip()
        if not uid and request.url.path not in {"/health", "/api/health"}:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authenticated tenant identity"},
            )
        token = set_tenant_uid(uid)
        try:
            return await call_next(request)
        finally:
            reset_tenant_uid(token)
