import type { Feed, FeedItem } from "./types.ts";
import { escapeHtml, escapeXml } from "./utils.ts";

export function toJsonFeed(feed: Feed, items: FeedItem[], baseUrl: string) {
  return {
    version: "https://jsonfeed.org/version/1.1",
    title: feed.name,
    home_page_url: `${baseUrl}/f/${feed.slug}`,
    feed_url: `${baseUrl}/f/${feed.slug}/feed.json`,
    description: feed.description,
    items: items.map((item) => ({ id: item.id, url: item.canonicalUrl || `${baseUrl}/f/${feed.slug}#${item.id}`, title: item.title, content_text: item.body, date_published: item.createdAt, authors: [{ name: feed.name }] })),
  };
}

export function toRss(feed: Feed, items: FeedItem[], baseUrl: string): string {
  const itemXml = items.map((item) => `<item><guid isPermaLink="false">${escapeXml(item.id)}</guid><title>${escapeXml(item.title || feed.name)}</title><description>${escapeXml(item.body)}</description><link>${escapeXml(item.canonicalUrl || `${baseUrl}/f/${feed.slug}#${item.id}`)}</link><pubDate>${new Date(item.createdAt).toUTCString()}</pubDate></item>`).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>${escapeXml(feed.name)}</title><link>${escapeXml(`${baseUrl}/f/${feed.slug}`)}</link><description>${escapeXml(feed.description)}</description>${itemXml}</channel></rss>`;
}

export function toMarkdownReport(feed: Feed, items: FeedItem[]): string {
  return `# ${feed.name}\n\n${feed.description}\n\n` + items.map((item, i) => `## ${i + 1}. ${item.title || "Signal"}\n\n${item.body}\n\n${item.provenance.map((p) => p.sourceUrl ? `- Source: ${p.sourceLabel || p.sourceType} — ${p.sourceUrl}` : `- Source: ${p.sourceLabel || p.sourceType}`).join("\n")}\n`).join("\n");
}

export function toPublicHtml(feed: Feed, items: FeedItem[]): string {
  const cards = items.map((item) => `<article id="${escapeHtml(item.id)}"><div class="meta">${escapeHtml(feed.emoji)} ${escapeHtml(feed.name)} · ${new Date(item.createdAt).toLocaleString()}</div>${item.title ? `<h2>${escapeHtml(item.title)}</h2>` : ""}<p>${escapeHtml(item.body)}</p><div class="prov">${item.provenance.length} source${item.provenance.length === 1 ? "" : "s"}</div></article>`).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(feed.name)} — Feedify</title><style>body{margin:0;background:#f7f7f4;color:#131313;font:16px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{max-width:720px;margin:auto;padding:48px 20px}header{padding:24px 0 34px}h1{font-size:42px;letter-spacing:-1.5px;margin:8px 0}.desc{font-size:18px;color:#65655f;line-height:1.5}article{background:white;border:1px solid #e9e9e4;border-radius:22px;padding:24px;margin:16px 0;box-shadow:0 8px 30px #00000008}article h2{font-size:22px;margin:12px 0}article p{font-size:17px;line-height:1.55;white-space:pre-wrap}.meta,.prov{font-size:13px;color:#81817a}.links a{color:#333;margin-right:16px}</style></head><body><div class="wrap"><header><div>FILTERFEED</div><h1>${escapeHtml(feed.emoji)} ${escapeHtml(feed.name)}</h1><div class="desc">${escapeHtml(feed.description)}</div><p class="links"><a href="/f/${feed.slug}/rss.xml">RSS</a><a href="/f/${feed.slug}/feed.json">JSON Feed</a><a href="/f/${feed.slug}/report.md">Report</a></p></header>${cards}</div></body></html>`;
}
