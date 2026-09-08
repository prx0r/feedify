import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

export async function fetchGetX(
  source: Extract<FeedSource, { type: "x_search" }>,
  options: { apiKey?: string; baseUrl?: string },
): Promise<Candidate[]> {
  if (!options.apiKey) return [];
  const base = (options.baseUrl || "https://api.getxapi.com").replace(/\/$/, "");
  const url = new URL(`${base}/twitter/tweet/advanced_search`);
  url.searchParams.set("q", source.query);
  url.searchParams.set("product", source.product || "Latest");
  const res = await fetch(url, { headers: { authorization: `Bearer ${options.apiKey}` }, signal: AbortSignal.timeout(12000) });
  if (!res.ok) throw new Error(`GetXAPI ${res.status}: ${await res.text()}`);
  const data = (await res.json()) as any;
  return (data.tweets || []).map((t: any) => ({
    id: stableId(source.id, String(t.id)),
    sourceId: source.id,
    sourceType: "x_search" as const,
    sourceLabel: source.label || "X",
    title: undefined,
    text: String(t.text || ""),
    url: t.url || t.twitterUrl,
    author: t.author?.userName ? `@${t.author.userName}` : undefined,
    publishedAt: t.createdAt,
    engagement: Number(t.likeCount || 0) + Number(t.retweetCount || 0) * 2 + Number(t.quoteCount || 0) * 2,
    metadata: { xId: t.id, author: t.author },
  }));
}
