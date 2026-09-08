export function stableId(...parts: string[]): string {
  let h = 2166136261;
  const input = parts.join("|");
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `ff_${(h >>> 0).toString(36)}`;
}

export function clamp(n: number, min = 0, max = 1): number {
  return Math.min(max, Math.max(min, n));
}

export function normalizeText(text: string): string {
  return text.toLowerCase().replace(/https?:\/\/\S+/g, "").replace(/[^\p{L}\p{N}\s]/gu, " ").replace(/\s+/g, " ").trim();
}

export function tokenSet(text: string): Set<string> {
  return new Set(normalizeText(text).split(" ").filter((x) => x.length > 2));
}

export function jaccard(a: string, b: string): number {
  const A = tokenSet(a), B = tokenSet(b);
  if (!A.size || !B.size) return 0;
  let intersection = 0;
  for (const x of A) if (B.has(x)) intersection++;
  return intersection / (A.size + B.size - intersection);
}

export function escapeXml(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&apos;");
}

export function escapeHtml(value: string): string {
  return escapeXml(value);
}
