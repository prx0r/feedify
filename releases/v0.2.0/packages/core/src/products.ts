import type { Feed, FeedProductManifest, OutputChannel } from "./types.ts";
import { stableId } from "./utils.ts";

export const OUTPUT_CATALOG = [
  {type:"feedify",name:"Feedify feed",kind:"native",description:"Subscribe, repost and discover inside Feedify."},
  {type:"public_web",name:"Public web",kind:"pull",description:"Beautiful canonical public feed page."},
  {type:"rss",name:"RSS",kind:"pull",description:"Portable RSS 2.0 feed."},
  {type:"json_feed",name:"JSON Feed",kind:"pull",description:"Machine-readable JSON Feed 1.1."},
  {type:"x_bot",name:"X bot",kind:"push",description:"Autopost new high-signal items to an X account."},
  {type:"webhook",name:"Webhook",kind:"push",description:"POST every new item to another system."},
  {type:"blog",name:"Blog",kind:"product",description:"Turn feed items into a persistent article stream."},
  {type:"report",name:"Reports",kind:"product",description:"Compile feed windows into Markdown research reports."},
  {type:"x402",name:"x402 API",kind:"paid",description:"Sell machine access to the feed over HTTP 402."},
  {type:"mcp",name:"MCP",kind:"agent",description:"Expose the feed directly to agents as MCP tools."},
] as const;

export function defaultOutputs(feed:Feed, now=new Date().toISOString()):OutputChannel[]{
  return ["feedify","public_web","rss","json_feed","mcp"].map((type)=>({
    id:stableId("output",feed.id,type),feedId:feed.id,type:type as OutputChannel["type"],name:OUTPUT_CATALOG.find(x=>x.type===type)!.name,enabled:true,config:{},createdAt:now,updatedAt:now
  }));
}

export function buildFeedManifest(feed:Feed,outputs:OutputChannel[],baseUrl:string):FeedProductManifest{
  const base=baseUrl.replace(/\/$/,"");
  const enriched=outputs.map((o)=>({id:o.id,type:o.type,name:o.name,enabled:o.enabled,
    href:o.type==="x402"?`${base}/paid/${feed.slug}/latest`:o.type==="mcp"?`${base}/mcp`:o.type==="rss"?`${base}/f/${feed.slug}/rss.xml`:o.type==="json_feed"?`${base}/f/${feed.slug}/feed.json`:o.type==="public_web"?`${base}/f/${feed.slug}`:undefined,
    price:o.type==="x402"?String(o.config.price||"$0.01"):undefined,network:o.type==="x402"?String(o.config.network||"eip155:8453"):undefined}));
  return {protocol:"feedify/1",feed:{id:feed.id,slug:feed.slug,name:feed.name,description:feed.description,emoji:feed.emoji,version:feed.version},canonical:`${base}/f/${feed.slug}`,endpoints:{api:`${base}/v1/feeds/${feed.slug}`,web:`${base}/f/${feed.slug}`,rss:`${base}/f/${feed.slug}/rss.xml`,jsonFeed:`${base}/f/${feed.slug}/feed.json`,report:`${base}/f/${feed.slug}/report.md`,mcp:`${base}/mcp`},outputs:enriched};
}

export function outputPublicConfig(output:OutputChannel){
  const hidden=new Set(["token","accessToken","secret","secretEnv","webhookSecret"]);
  return Object.fromEntries(Object.entries(output.config).filter(([k])=>!hidden.has(k)));
}
