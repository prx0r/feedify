import type { FeedItem, OutputChannel } from "@feedify/core";

function xSourceId(item:FeedItem){
  const p=item.provenance.find((x)=>x.sourceType==="x_search" && x.sourceItemId);
  return p?.sourceItemId && /^\d+$/.test(p.sourceItemId) ? p.sourceItemId : undefined;
}

export function renderXPost(item: FeedItem, config:Record<string,unknown>={}) {
  const includeSource=config.includeSourceLink!==false;
  const provenance = includeSource ? item.provenance.find((p) => p.sourceUrl)?.sourceUrl : undefined;
  let text = `${item.title ? `${item.title}\n\n` : ""}${item.body}`;
  if (provenance && item.kind !== "source") text += `\n\n${provenance}`;
  if (text.length > 275) text = `${text.slice(0, 272)}…`;
  return text;
}

export async function publishToX(item: FeedItem, output:OutputChannel, env:NodeJS.ProcessEnv=process.env) {
  const config=output.config||{};
  const tokenEnv=String(config.tokenEnv||"X_USER_ACCESS_TOKEN");
  const userIdEnv=String(config.userIdEnv||"X_USER_ID");
  const accessToken=env[tokenEnv];
  const userId=env[userIdEnv];
  const baseUrl=String(config.baseUrl||env.X_API_BASE_URL||"https://api.x.com/2").replace(/\/$/,"");
  const sourceId=xSourceId(item);
  const configured=String(config.strategy||"smart");
  const strategy=configured==="smart" ? (sourceId && item.kind==="source" ? "repost" : (sourceId && config.allowQuote===true ? "quote" : "post")) : configured;
  const text=renderXPost(item,config);

  if(config.dryRun===true || !accessToken){return {dryRun:true,strategy,text,sourceId,reason:!accessToken?`${tokenEnv} not configured`:"output dryRun enabled"};}
  if(strategy==="repost"){
    if(!sourceId)throw new Error("X repost requested but item has no original X post id");
    if(!userId)throw new Error(`${userIdEnv} is required for X repost output`);
    const res=await fetch(`${baseUrl}/users/${encodeURIComponent(userId)}/retweets`,{method:"POST",headers:{authorization:`Bearer ${accessToken}`,"content-type":"application/json"},body:JSON.stringify({tweet_id:sourceId})});
    if(!res.ok)throw new Error(`X repost ${res.status}: ${await res.text()}`);
    return {strategy,data:await res.json()};
  }
  const payload:any={text};
  if(strategy==="quote"){
    if(!sourceId)throw new Error("X quote requested but item has no original X post id");
    payload.quote_tweet_id=sourceId;
  }
  const res=await fetch(`${baseUrl}/tweets`,{method:"POST",headers:{authorization:`Bearer ${accessToken}`,"content-type":"application/json"},body:JSON.stringify(payload)});
  if(!res.ok)throw new Error(`X publish ${res.status}: ${await res.text()}`);
  return {strategy,data:await res.json()};
}
