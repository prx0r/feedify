# Feedify 0.2 test report — 2026-09-08

## Passed locally

1. `tsc --noEmit -p packages/core/tsconfig.json`
2. `tsc --noEmit -p packages/sdk/tsconfig.json` (with local workspace link)
3. `node --experimental-transform-types scripts/smoke-test.mjs`
   - stable IDs / similarity sanity
   - output catalog includes X/x402/MCP
   - product manifest generation
   - original + product-chain migrations present
4. `node --experimental-transform-types scripts/advanced-test.mjs`
   - mocked GitHub repository source adapter
   - mocked generic JSON API source adapter
   - smart X output selects repost for a source X item
   - smart X output selects normal post for transformed content (quote-post is opt-in)
   - webhook dry-run delivery path
5. Booted the real core API with a fresh temporary JSON database and exercised:
   - `/health`
   - `/v1/feeds/shopify-alpha/manifest`
   - `/v1/feeds/shopify-alpha/products`
   - `/v1/feeds/shopify-alpha/chain`
   - adding a webhook product without changing the feed
   - seeded X-bot product publish as dry-run
6. Booted the real core API and exercised `@feedify/sdk`:
   - list feeds
   - latest Tantrāloka item
   - Shopify Alpha manifest containing x402 output

## Not executable in this container

The container cannot resolve/reach npm, so fresh third-party gateway packages could not be installed. Therefore these files were validated against current official documentation/repository APIs but not booted here:

- `apps/x402-gateway` — official `@x402/core`, `@x402/express`, `@x402/evm`
- `apps/mcp-gateway` — official MCP v2 packages implementing the 2026-07-28 protocol
- Expo mobile runtime (requires Expo/React Native dependencies)

The core Feedify API, SDK and dependency-free tests are runnable without those gateway dependencies once normal `npm install` access is available.

## Current X caveat

X's current create-post docs state that API quote-post creation is Enterprise-only. Feedify therefore does **not** choose quote-post in `smart` mode by default. It uses repost for raw X source items and normal posts with provenance for transformed items. `allowQuote: true` is explicit opt-in for an eligible X plan.
