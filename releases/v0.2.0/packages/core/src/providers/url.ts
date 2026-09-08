import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

function strip(html: string): string {
  return html.replace(/<script\b[\s\S]*?<\/script>/gi, " ").replace(/<style\b[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
}

export async function fetchUrl(source: Extract<FeedSource, {type:"url"}>): Promise<Candidate[]> {
  const res = await fetch(source.url, { headers: { "user-agent": "Feedify/0.1 (+https://feedify.dev)" }, signal: AbortSignal.timeout(12000) });
  if (!res.ok) throw new Error(`URL fetch ${res.status}: ${source.url}`);
  const html = await res.text();
  const title = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/\s+/g, " ").trim();
  const description = html.match(/<meta[^>]+(?:name|property)=["'](?:description|og:description)["'][^>]+content=["']([^"']+)["']/i)?.[1];
  const text = description || strip(html).slice(0, 6000);
  return [{ id: stableId(source.id, source.url, text.slice(0, 100)), sourceId: source.id, sourceType: "url", sourceLabel: source.label, title, text, url: source.url }];
}
