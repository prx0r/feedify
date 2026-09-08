import type { Candidate, FeedProgram } from "./types.ts";

export class AIClient {
  constructor(
    private readonly options: {
      baseUrl?: string;
      apiKey?: string;
      model?: string;
    } = {},
  ) {}

  get enabled(): boolean {
    return Boolean(this.options.apiKey);
  }

  async json<T>(system: string, user: string): Promise<T> {
    if (!this.options.apiKey) throw new Error("AI provider not configured");
    const base = (this.options.baseUrl || "https://api.openai.com/v1").replace(/\/$/, "");
    const res = await fetch(`${base}/chat/completions`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${this.options.apiKey}` },
      body: JSON.stringify({
        model: this.options.model || "gpt-5-mini",
        temperature: 0.2,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: system },
          { role: "user", content: user },
        ],
      }),
    });
    if (!res.ok) throw new Error(`AI request failed: ${res.status} ${await res.text()}`);
    const data = (await res.json()) as any;
    const content = data.choices?.[0]?.message?.content;
    if (!content) throw new Error("AI provider returned no content");
    return JSON.parse(content) as T;
  }
}

export async function aiTransform(
  ai: AIClient,
  program: FeedProgram,
  candidates: Candidate[],
  feedName: string,
): Promise<{ title?: string; body: string; usedCandidateIds: string[] }> {
  if (!ai.enabled) {
    const first = candidates[0];
    return {
      title: first?.title,
      body: first ? distillFallback(first.text, program.voice) : `A new ${feedName} insight will appear when sources produce enough signal.`,
      usedCandidateIds: first ? [first.id] : [],
    };
  }
  const payload = candidates.slice(0, 8).map((c) => ({ id: c.id, title: c.title, text: c.text, url: c.url, author: c.author }));
  return ai.json(
    `You are the publishing engine for a source-grounded feed called ${feedName}. Never fabricate quotations or citations. Return JSON with title, body, usedCandidateIds. The body should be concise enough for a premium mobile feed.`,
    JSON.stringify({ program, candidates: payload }),
  );
}

function distillFallback(text: string, voice?: string): string {
  const clean = text.replace(/\s+/g, " ").trim();
  const clipped = clean.length > 520 ? `${clean.slice(0, 517)}…` : clean;
  return voice ? `${clipped}` : clipped;
}
