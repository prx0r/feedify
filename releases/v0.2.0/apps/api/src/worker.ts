import { resolve } from "node:path";
import { AIClient, runFeed } from "@feedify/core";
import { JsonRepository } from "./repository.ts";
import { dispatchOutput } from "./output-dispatcher.ts";

const repo=new JsonRepository(resolve(process.env.DATA_FILE||"./data/feedify.json"));
const ai=new AIClient({baseUrl:process.env.OPENAI_BASE_URL,apiKey:process.env.OPENAI_API_KEY,model:process.env.OPENAI_MODEL});
const once=process.argv.includes("--once") || process.env.WORKER_ONCE==="1";
const intervalMs=Math.max(60_000,Number(process.env.FEEDIFY_RUN_INTERVAL_MS||900_000));

async function tick(){
  const feeds=await repo.listFeeds("worker");
  for(const feed of feeds){
    try{
      const prior=await repo.itemsForFeed(feed.id,200);
      const items=await runFeed({feed,priorItems:prior,ai,env:{getxApiKey:process.env.GETX_API_KEY,getxBaseUrl:process.env.GETX_BASE_URL,githubToken:process.env.GITHUB_TOKEN,githubBaseUrl:process.env.GITHUB_BASE_URL}});
      if(!items.length)continue;
      await repo.saveItems(items);
      const all=await repo.itemsForFeed(feed.id,100);const outputs=await repo.outputsForFeed(feed.id);
      for(const output of outputs.filter((o)=>o.enabled)){
        const deliveries=await dispatchOutput({feed,items,output,allFeedItems:all,env:process.env});
        for(const d of deliveries){await repo.recordDelivery(d);if(d.status==="success"&&d.itemId)await repo.markPublished(d.itemId,output.id);}
      }
      console.log(JSON.stringify({feed:feed.slug,created:items.length}));
    }catch(error:any){console.error(JSON.stringify({feed:feed.slug,error:error?.message||String(error)}));}
  }
}

await tick();
if(!once)setInterval(()=>void tick(),intervalMs);
