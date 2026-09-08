import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

function decodeXml(s: string): string {
  return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function tag(block: string, names: string[]): string | undefined {
  for (const name of names) {
    const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${name}>`, "i"));
    if (m) return decodeXml(m[1]);
  }
}

function attr(block: string, tagName: string, attrName: string): string | undefined {
  const m = block.match(new RegExp(`<${tagName}[^>]*${attrName}=["']([^"']+)["'][^>]*>`, "i"));
  return m?.[1];
}

export function parseFeedXml(xml: string, source: Extract<FeedSource, {type:"rss"}>): Candidate[] {
  const itemBlocks = [...xml.matchAll(/<item\b[\s\S]*?<\/item>/gi)].map((m) => m[0]);
  const entryBlocks = [...xml.matchAll(/<entry\b[\s\S]*?<\/entry>/gi)].map((m) => m[0]);
  return [...itemBlocks, ...entryBlocks].slice(0, 50).map((block) => {
    const title = tag(block, ["title"]);
    const text = tag(block, ["content:encoded", "content", "summary", "description"]) || title || "";
    const url = tag(block, ["link"]) || attr(block, "link", "href");
    const publishedAt = tag(block, ["pubDate", "published", "updated"]);
    const author = tag(block, ["author", "dc:creator", "name"]);
    const extId = tag(block, ["guid", "id"]) || url || `${title}:${publishedAt}`;
    return { id: stableId(source.id, extId || text), sourceId: source.id, sourceType: "rss" as const, sourceLabel: source.label, title, text, url, author, publishedAt };
  }).filter((x) => x.text.length > 0);
}

export async function fetchRss(source: Extract<FeedSource, {type:"rss"}>): Promise<Candidate[]> {
  const res = await fetch(source.url, { headers: { "user-agent": "Feedify/0.1 (+https://feedify.dev)" }, signal: AbortSignal.timeout(12000) });
  if (!res.ok) throw new Error(`RSS fetch ${res.status}: ${source.url}`);
  return parseFeedXml(await res.text(), source);
}
