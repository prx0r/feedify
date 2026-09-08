import type { Candidate, FeedSource } from "../types.ts";
import { fetchCorpus } from "./corpus.ts";
import { fetchGetX } from "./getx.ts";
import { fetchRss } from "./rss.ts";
import { fetchUrl } from "./url.ts";
import { fetchGitHub } from "./github.ts";
import { fetchJsonApi } from "./json-api.ts";

export type SourceEnv={getxApiKey?:string;getxBaseUrl?:string;githubToken?:string;githubBaseUrl?:string};
export async function fetchSource(source: FeedSource, env: SourceEnv): Promise<Candidate[]> {
  switch (source.type) {
    case "rss": return fetchRss(source);
    case "url": return fetchUrl(source);
    case "x_search": return fetchGetX(source, { apiKey: env.getxApiKey, baseUrl: env.getxBaseUrl });
    case "github_search": return fetchGitHub(source,{githubToken:env.githubToken,githubBaseUrl:env.githubBaseUrl});
    case "json_api": return fetchJsonApi(source);
    case "corpus": return fetchCorpus(source);
  }
}
