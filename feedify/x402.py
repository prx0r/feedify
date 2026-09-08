"""Optional x402 protection for machine-readable paid feeds."""
from __future__ import annotations

from typing import Any

from feedify.settings import get_settings


def x402_config() -> dict[str, Any]:
    s = get_settings()
    return {
        "enabled": s.x402_enabled,
        "pay_to": s.x402_pay_to,
        "network": s.x402_network,
        "price_usd": s.x402_price_usd,
        "facilitator_url": s.x402_facilitator_url,
    }


def install_x402(app) -> bool:
    """Attach official x402 v2 ASGI middleware when explicitly enabled.

    Local development remains payment-free. Production can expose the exact same feed
    through /api/paid/* and charge agents per request.
    """
    s = get_settings()
    if not s.x402_enabled:
        return False
    if not s.x402_pay_to:
        raise RuntimeError("X402_ENABLED=true requires X402_PAY_TO")
    try:
        from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
        from x402.http.middleware.fastapi import PaymentMiddlewareASGI
        from x402.http.types import RouteConfig
        from x402.mechanisms.evm.exact import ExactEvmServerScheme
        from x402.server import x402ResourceServer
    except ImportError as exc:
        raise RuntimeError('x402 support requires: uv sync --extra x402') from exc

    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=s.x402_facilitator_url))
    server = x402ResourceServer(facilitator)
    server.register(s.x402_network, ExactEvmServerScheme())
    routes = {
        "GET /api/paid/*": RouteConfig(
            accepts=[
                PaymentOption(
                    scheme="exact",
                    pay_to=s.x402_pay_to,
                    price=f"${s.x402_price_usd:.4f}",
                    network=s.x402_network,
                )
            ],
            mime_type="application/json",
            description="Paid Feedify machine-readable intelligence feed",
        )
    }
    app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)
    return True
