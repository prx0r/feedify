import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

export async function fetchCorpus(source: Extract<FeedSource, {type:"corpus"}>): Promise<Candidate[]> {
  return source.items.map((item) => ({
    id: stableId(source.id, item.id),
    sourceId: source.id,
    sourceType: "corpus" as const,
    sourceLabel: source.label,
    title: item.title,
    text: item.text,
    url: item.url,
    metadata: { citation: item.citation },
  }));
}
