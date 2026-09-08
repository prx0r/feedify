import { createHmac } from "node:crypto";
import type { Feed, FeedItem, OutputChannel, OutputDelivery } from "@feedify/core";
import { stableId, toMarkdownReport } from "@feedify/core";
import { publishToX } from "./x-publisher.ts";

export type DispatchContext={feed:Feed;items:FeedItem[];output:OutputChannel;allFeedItems:FeedItem[];env?:NodeJS.ProcessEnv};

function delivery(output:OutputChannel,item:FeedItem|undefined,status:OutputDelivery["status"],detail?:string,externalId?:string):OutputDelivery{
  const createdAt=new Date().toISOString();
  return {id:stableId("delivery",output.id,item?.id||"batch",createdAt),outputId:output.id,feedId:output.feedId,itemId:item?.id,status,detail,externalId,createdAt};
}

async function postWebhook(ctx:DispatchContext,item:FeedItem){
  const url=String(ctx.output.config.url||"");if(!url)throw new Error("webhook output requires config.url");
  const payload=JSON.stringify({event:"feedify.item.created",feed:ctx.feed,item});
  const headers:Record<string,string>={"content-type":"application/json","user-agent":"Feedify/0.2 (+https://feedify.dev)"};
  const secretEnv=String(ctx.output.config.secretEnv||"FEEDIFY_WEBHOOK_SECRET");const secret=(ctx.env||process.env)[secretEnv];
  if(secret)headers["x-feedify-signature"]=`sha256=${createHmac("sha256",secret).update(payload).digest("hex")}`;
  if(ctx.output.config.dryRun===true)return {dryRun:true,url,payload};
  const res=await fetch(url,{method:"POST",headers,body:payload,signal:AbortSignal.timeout(15000)});if(!res.ok)throw new Error(`webhook ${res.status}: ${await res.text()}`);return {status:res.status};
}

export async function dispatchOutput(ctx:DispatchContext):Promise<OutputDelivery[]>{
  if(!ctx.output.enabled)return [];
  if(["feedify","public_web","rss","json_feed","mcp","x402"].includes(ctx.output.type))return [];
  if(ctx.output.type==="report"){
    const report=toMarkdownReport(ctx.feed,ctx.allFeedItems.slice(0,50));
    return [delivery(ctx.output,undefined,"dry_run",`report-ready:${Buffer.byteLength(report)}b`)];
  }
  if(ctx.output.type==="blog"){
    return ctx.items.map((item)=>delivery(ctx.output,item,"dry_run",`blog-ready:${item.feedSlug}/${item.id}.md`));
  }
  const out:OutputDelivery[]=[];
  for(const item of ctx.items){
    try{
      if(ctx.output.type==="x_bot"){
        const result:any=await publishToX(item,ctx.output,ctx.env||process.env);
        const ext=result?.data?.data?.id;out.push(delivery(ctx.output,item,result?.dryRun?"dry_run":"success",JSON.stringify({strategy:result.strategy}),ext));
      }else if(ctx.output.type==="webhook"){
        const result:any=await postWebhook(ctx,item);out.push(delivery(ctx.output,item,result?.dryRun?"dry_run":"success",result?.dryRun?"webhook dry run":undefined));
      }
    }catch(err:any){out.push(delivery(ctx.output,item,"failed",err?.message||String(err)));}
  }
  return out;
}
