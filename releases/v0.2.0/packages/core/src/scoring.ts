import type { Candidate, FeedItem, FeedProgram, ScoreBreakdown } from "./types.ts";
import { clamp, jaccard, normalizeText, tokenSet } from "./utils.ts";

function keywordAffinity(text: string, terms: string[]): number {
  if (!terms.length) return 0.6;
  const normalized = normalizeText(text);
  let hits = 0;
  for (const term of terms) if (normalized.includes(normalizeText(term))) hits++;
  return clamp(hits / Math.max(1, Math.min(terms.length, 4)));
}

function actionability(text: string): number {
  const t = normalizeText(text);
  const actionTerms = ["launch", "released", "api", "github", "open source", "available", "build", "new", "changed", "guide", "implementation", "dataset", "protocol"];
  return clamp(actionTerms.filter((x) => t.includes(x)).length / 4 + 0.25);
}

function quality(candidate: Candidate): number {
  const length = tokenSet(candidate.text).size;
  const depth = clamp(length / 80);
  const engagement = candidate.engagement ? clamp(Math.log10(candidate.engagement + 1) / 5) : 0.25;
  return clamp(0.65 * depth + 0.35 * engagement);
}

export function scoreCandidate(candidate: Candidate, program: FeedProgram, priorItems: FeedItem[]): ScoreBreakdown {
  const combined = `${candidate.title ?? ""} ${candidate.text}`;
  const inclusion = keywordAffinity(combined, [...program.include, ...program.rankFor]);
  const exclusion = keywordAffinity(combined, program.exclude);
  const relevance = clamp(inclusion - exclusion * 0.9 + 0.25);
  let maxSimilarity = 0;
  for (const item of priorItems.slice(0, 200)) maxSimilarity = Math.max(maxSimilarity, jaccard(combined, `${item.title ?? ""} ${item.body}`));
  const novelty = clamp(1 - maxSimilarity);
  const q = quality(candidate);
  const act = actionability(combined);
  const total = clamp(0.35 * relevance + program.noveltyWeight * 0.25 * novelty + 0.2 * q + 0.2 * act);
  return { relevance, novelty, quality: q, actionability: act, total };
}

export function dedupeCandidates(candidates: Candidate[]): Candidate[] {
  const out: Candidate[] = [];
  for (const c of candidates) {
    if (out.some((x) => x.url && c.url && x.url === c.url)) continue;
    if (out.some((x) => jaccard(`${x.title ?? ""} ${x.text}`, `${c.title ?? ""} ${c.text}`) > 0.86)) continue;
    out.push(c);
  }
  return out;
}
