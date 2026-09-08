import { AIClient, aiTransform } from "./ai.ts";
import { dedupeCandidates, scoreCandidate } from "./scoring.ts";
import type { Candidate, Feed, FeedItem, Provenance } from "./types.ts";
import { stableId } from "./utils.ts";
import { fetchSource } from "./providers/index.ts";

export async function runFeed(input: {
  feed: Feed;
  priorItems: FeedItem[];
  ai: AIClient;
  env: { getxApiKey?: string; getxBaseUrl?: string; githubToken?: string; githubBaseUrl?: string };
}): Promise<FeedItem[]> {
  const settled = await Promise.allSettled(input.feed.sources.map((s) => fetchSource(s, input.env)));
  const candidates = dedupeCandidates(settled.flatMap((r) => r.status === "fulfilled" ? r.value : []));
  const scored = candidates
    .map((candidate) => ({ candidate, scores: scoreCandidate(candidate, input.feed.program, input.priorItems) }))
    .filter((x) => x.scores.total >= input.feed.program.minScore)
    .sort((a, b) => b.scores.total - a.scores.total);

  if (input.feed.program.mode === "curate") {
    return scored.slice(0, input.feed.program.maxItemsPerRun).map(({ candidate, scores }) => candidateToItem(input.feed, candidate, scores));
  }

  const chosen = scored.slice(0, 8).map((x) => x.candidate);
  if (!chosen.length && candidates.length) chosen.push(candidates[0]);
  const transformed = await aiTransform(input.ai, input.feed.program, chosen, input.feed.name);
  const used = transformed.usedCandidateIds.map((id) => chosen.find((x) => x.id === id)).filter(Boolean) as Candidate[];
  const evidence = used.length ? used : chosen.slice(0, 3);
  const signature = `${input.feed.version}|${transformed.title || ""}|${transformed.body}`;
  if (input.priorItems.some((x) => x.id === stableId(input.feed.id, signature))) return [];
  return [{
    id: stableId(input.feed.id, signature),
    feedId: input.feed.id,
    feedSlug: input.feed.slug,
    feedName: input.feed.name,
    feedEmoji: input.feed.emoji,
    feedVersion: input.feed.version,
    kind: input.feed.program.mode === "distill" ? "summary" : input.feed.program.mode === "synthesize" ? "synthesis" : "generated",
    title: transformed.title,
    body: transformed.body,
    provenance: evidence.map(toProvenance),
    createdAt: new Date().toISOString(),
    repostCount: 0, likeCount: 0, commentCount: 0,
  }];
}

function candidateToItem(feed: Feed, candidate: Candidate, scores: any): FeedItem {
  return {
    id: stableId(feed.id, candidate.id),
    feedId: feed.id, feedSlug: feed.slug, feedName: feed.name, feedEmoji: feed.emoji, feedVersion: feed.version,
    kind: "source", title: candidate.title, body: candidate.text, canonicalUrl: candidate.url,
    provenance: [toProvenance(candidate)], scores, createdAt: candidate.publishedAt || new Date().toISOString(),
    repostCount: 0, likeCount: 0, commentCount: 0,
  };
}

function toProvenance(c: Candidate): Provenance {
  return { sourceId: c.sourceId, sourceType: c.sourceType, sourceLabel: c.sourceLabel || c.author, sourceUrl: c.url, sourceItemId: String(c.metadata?.xId || c.id), excerpt: c.text.slice(0, 280) };
}
