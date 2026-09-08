# Deployment topology

Recommended initial topology:

```text
feedify.dev / mobile app
        |
api.feedify.dev  (core API)
        |
        +-- worker / scheduler
        +-- x.feedify.dev builder UI
        +-- git.feedify.dev builder UI
        +-- mcp.feedify.dev/mcp  (MCP gateway)
        +-- paid.feedify.dev     (x402 gateway)
```

The subdomain UIs can be very thin because feed compilation and product manifests live in the core API.

## Minimum secrets

Core API: AI key (optional), GetXAPI key (for X source feeds), GitHub token (recommended).

X bot: official X user OAuth access token + X user id.

x402: pay-to wallet plus optional facilitator override.

Webhook: HMAC secret if signatures are desired.
