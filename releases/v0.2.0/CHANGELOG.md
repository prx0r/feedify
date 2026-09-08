# Changelog

## 0.2.0 — Feedify product-chain MVP

- renamed product/package surface from Filterfeed to Feedify while preserving migration history
- added first-class `OutputChannel` / `OutputDelivery`
- added source→feed→product graph and machine manifest
- added x.feedify.dev / git.feedify.dev machine-readable templates
- added native GitHub repository and generic JSON API sources
- added smart X bot post/repost/optional-quote wiring
- added signed webhook output
- added blog/report materialization hooks
- added official x402 gateway app for paid feed endpoints
- added Feedify SDK shared by gateways
- added official MCP v2 agent gateway
- added worker loop that runs a feed once then dispatches the same items to outputs
- added mobile Products screen and one-tap output creation
- added Supabase product-chain migration and delivery audit model
- expanded regression tests and deployment docs
