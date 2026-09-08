import { AIClient } from "./ai.ts";
import type { FeedProgram } from "./types.ts";

const STOP = new Set(["the","a","an","and","or","to","of","in","on","for","with","my","me","i","it","is","are","be","that","this","just","from","into"]);

export async function compileFeedPrompt(ai: AIClient, prompt: string): Promise<FeedProgram> {
  if (ai.enabled) {
    try {
      return await ai.json<FeedProgram>(
        "Compile a natural-language request into a Feedify FeedProgram JSON object. mode must be curate, distill, synthesize, or generate. minScore 0..1, sourceStrictness 0..1, noveltyWeight 0..1. Keep include/exclude/rankFor concise.",
        prompt,
      );
    } catch (error) {
      console.warn("AI compilation failed, using heuristic compiler", error);
    }
  }
  return heuristicCompile(prompt);
}

export function heuristicCompile(prompt: string): FeedProgram {
  const words = prompt.toLowerCase().match(/[a-z0-9āīūṛṝḷṃḥśṣñṅṭḍṇ]+/g) || [];
  const ranked = [...new Set(words.filter((w) => w.length > 4 && !STOP.has(w)))].slice(0, 8);
  const p = prompt.toLowerCase();
  const mode: FeedProgram["mode"] = p.includes("distill") || p.includes("daily insight")
    ? "distill"
    : p.includes("generate") || p.includes("posting") || p.includes("character")
      ? "generate"
      : p.includes("synth") || p.includes("connect")
        ? "synthesize"
        : "curate";
  return {
    objective: prompt.trim(),
    mode,
    include: ranked,
    exclude: ["generic", "engagement bait", "recycled"],
    rankFor: ["novelty", "specificity", "source evidence", "actionability"],
    voice: p.includes("funny") ? "dry, concise, playful without sacrificing source fidelity" : "clear, concise, high-signal",
    maxItemsPerRun: mode === "curate" ? 8 : 1,
    minScore: 0.48,
    sourceStrictness: p.includes("source") || p.includes("text") || p.includes("tantra") ? 0.95 : 0.75,
    noveltyWeight: 0.9,
  };
}
