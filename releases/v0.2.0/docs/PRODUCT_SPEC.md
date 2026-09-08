# Feedify MVP product spec

## Product primitive
A Feed is a versioned program that converts a source universe into an ordered stream of immutable FeedItems.

## Modes
- **curate** — select source items without rewriting them.
- **distill** — convert source material into concise source-grounded insights.
- **synthesize** — combine multiple sources into a new higher-level signal.
- **generate** — create an ongoing character/editorial feed while retaining provenance constraints.

## Primary mobile surfaces
1. **Home** — finite signal timeline.
2. **Explore** — subscribe to public feeds.
3. **Create** — natural-language feed compiler.
4. **You** — owned/subscribed feeds and personal signal stats.
5. **Feed detail** — follow, provenance, feed history.

## Social verbs
- Follow feed
- Repost item
- Quote repost (API model implemented; dedicated composer is next)
- Useful / already knew / noise / too late / actioned feedback

## Creator outputs
Every feed can compile to multiple output channels. MVP includes public HTML, RSS, JSON Feed, report Markdown and X publishing.

## Next intelligent features
- Per-user knowledge frontier from `already_knew` feedback.
- Source lead-time / origin tracing.
- Cross-feed collision alerts.
- Signal budgets and "nothing happened" states.
- Feed forking/version lineage.
- Corpus upload/extraction + paragraph-level citations.
- Creator feed marketplace.
