# Reuse research — Feedify 0.2

The MVP extends existing Feedify code and uses upstream packages/protocols rather than copying competing source trees.

## Mobile/social
- Expo SDK 57: current React Native / Expo Router baseline.
- bluesky-social/social-app: production reference for a feed-centric React Native social client.
- bluesky-social/feed-generator: validates separating an algorithmic feed from the client that consumes it.

## Payments
- x402-foundation/x402: official x402 implementation. Current TypeScript distribution includes `@x402/core`, `@x402/express`, EVM/SVM mechanisms, paywall, MCP and client integrations. Feedify's x402 gateway is designed around the official middleware rather than recreating verify/settle behavior.

## Agents
- modelcontextprotocol/typescript-sdk: current v2 SDK implements the 2026-07-28 MCP spec. Feedify uses the v2 server entry (`createMcpHandler`) in its agent gateway.

## Feeds
- JSON Feed 1.1: simple JSON-native portable feed format (`application/feed+json`).
- RSS 2.0 / Atom: broad reader compatibility.
- FreshRSS: useful product/OPML/WebSub reference, but its AGPL implementation is not copied.

## X
- GetXAPI: inexpensive search/ingestion adapter for the source side.
- Official X API: write/repost side to avoid binding Feedify publishing to a session-scraping implementation.
