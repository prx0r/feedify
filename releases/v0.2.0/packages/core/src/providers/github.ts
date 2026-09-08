import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

type GitHubSource = Extract<FeedSource, {type:"github_search"}>;

export async function fetchGitHub(source: GitHubSource, env: { githubToken?: string; githubBaseUrl?: string }): Promise<Candidate[]> {
  const base=(env.githubBaseUrl||"https://api.github.com").replace(/\/$/,"");
  const params=new URLSearchParams({q:source.query,sort:source.sort||"updated",order:source.order||"desc",per_page:"30"});
  const headers:Record<string,string>={"accept":"application/vnd.github+json","user-agent":"Feedify/0.2 (+https://feedify.dev)","x-github-api-version":"2022-11-28"};
  if(env.githubToken)headers.authorization=`Bearer ${env.githubToken}`;
  const res=await fetch(`${base}/search/repositories?${params}`,{headers,signal:AbortSignal.timeout(12000)});
  if(!res.ok)throw new Error(`GitHub search ${res.status}: ${await res.text()}`);
  const json:any=await res.json();
  return (Array.isArray(json.items)?json.items:[]).map((repo:any)=>({
    id:stableId(source.id,String(repo.id||repo.full_name)),sourceId:source.id,sourceType:"github_search" as const,sourceLabel:source.label||"GitHub",
    title:repo.full_name,text:[repo.description,`★ ${repo.stargazers_count||0}`,repo.language?`Language: ${repo.language}`:null].filter(Boolean).join(" · "),
    url:repo.html_url,author:repo.owner?.login,publishedAt:repo.updated_at,engagement:Number(repo.stargazers_count||0),metadata:{stars:repo.stargazers_count,forks:repo.forks_count,language:repo.language,topics:repo.topics}
  })).filter((x:any)=>x.text);
}
