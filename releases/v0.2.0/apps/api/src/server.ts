import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { dirname, resolve } from "node:path";
import { mkdir, writeFile } from "node:fs/promises";
import { URL } from "node:url";
import {
  AIClient, OUTPUT_CATALOG, buildFeedManifest, compileFeedPrompt, outputPublicConfig, runFeed, stableId,
  toJsonFeed, toMarkdownReport, toPublicHtml, toRss,
  type Feed, type FeedbackValue, type OutputChannel, type OutputType,
} from "@feedify/core";
import { JsonRepository } from "./repository.ts";
import { seedDatabase } from "./seed-data.ts";
import { dispatchOutput } from "./output-dispatcher.ts";

const port=Number(process.env.PORT||8787);
const dataFile=resolve(process.env.DATA_FILE||"./data/feedify.json");
const publicBase=(process.env.PUBLIC_BASE_URL||`http://localhost:${port}`).replace(/\/$/,"");
const x402Base=(process.env.X402_PUBLIC_BASE_URL||publicBase).replace(/\/$/,"");
const mcpBase=(process.env.MCP_PUBLIC_BASE_URL||publicBase).replace(/\/$/,"");
const repo=new JsonRepository(dataFile);
const ai=new AIClient({baseUrl:process.env.OPENAI_BASE_URL,apiKey:process.env.OPENAI_API_KEY,model:process.env.OPENAI_MODEL});

async function ensureSeed(){if((await repo.listFeeds()).length===0){await mkdir(dirname(dataFile),{recursive:true});await writeFile(dataFile,JSON.stringify(seedDatabase,null,2));}}
await ensureSeed();

function send(res:ServerResponse,status:number,data:any,type="application/json; charset=utf-8"){
  res.writeHead(status,{"content-type":type,"access-control-allow-origin":"*","access-control-allow-headers":"content-type,authorization,x-feedify-user,x-feedify-admin","access-control-allow-methods":"GET,POST,OPTIONS"});
  res.end(type.includes("json")?JSON.stringify(data):String(data));
}
async function body(req:IncomingMessage){let raw="";for await(const chunk of req)raw+=chunk;return raw?JSON.parse(raw):{};}
function userId(req:IncomingMessage){return String(req.headers["x-feedify-user"]||"demo");}
function slugify(s:string){return s.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,64)||`feed-${Date.now()}`;}
function withPublicBases(manifest:any){
  manifest.endpoints.mcp=`${mcpBase}/mcp`;
  for(const o of manifest.outputs){if(o.type==="mcp")o.href=`${mcpBase}/mcp`;if(o.type==="x402")o.href=`${x402Base}/paid/${manifest.feed.slug}/latest`;}
  return manifest;
}
async function manifestFor(feed:Feed){return withPublicBases(buildFeedManifest(feed,await repo.outputsForFeed(feed.id),publicBase));}
async function dispatch(feed:Feed,items:any[]){
  if(!items.length)return [];
  const outputs=await repo.outputsForFeed(feed.id);const all=await repo.itemsForFeed(feed.id,100);const deliveries=[];
  for(const output of outputs.filter((x)=>x.enabled)){
    const d=await dispatchOutput({feed,items,output,allFeedItems:all,env:process.env});for(const x of d){await repo.recordDelivery(x);if(x.itemId&&x.status==="success")await repo.markPublished(x.itemId,output.id);}deliveries.push(...d);
  }
  return deliveries;
}
function outputName(type:OutputType){return OUTPUT_CATALOG.find((x)=>x.type===type)?.name||type;}

const templates={
  x:{host:"x.feedify.dev",title:"X → Feed",description:"Prompt an X signal algorithm, preview it, then publish it as a Feedify feed, X bot or x402 endpoint.",source:{type:"x_search",query:"<your X query>",product:"Latest"},suggestedOutputs:["feedify","x_bot","x402","rss","json_feed"]},
  git:{host:"git.feedify.dev",title:"Git → Feed",description:"Turn GitHub repository discovery into a ranked technical-alpha feed and machine endpoint.",source:{type:"github_search",query:"stars:>20 pushed:>YYYY-MM-DD",sort:"updated",order:"desc"},suggestedOutputs:["feedify","x_bot","x402","rss","json_feed","mcp"]},
  corpus:{host:"feedify.dev",title:"Corpus → Feed",description:"Turn a bounded source corpus into a source-grounded ongoing insight stream.",source:{type:"corpus"},suggestedOutputs:["feedify","blog","report","x402","rss","mcp"]},
};

const server=createServer(async(req,res)=>{
  try{
    if(req.method==="OPTIONS")return send(res,204,"");
    const url=new URL(req.url||"/",publicBase);const path=url.pathname;const uid=userId(req);

    if(req.method==="GET"&&path==="/health")return send(res,200,{ok:true,product:"Feedify",version:"0.2.0",ai:ai.enabled,getx:Boolean(process.env.GETX_API_KEY),github:Boolean(process.env.GITHUB_TOKEN),x:Boolean(process.env.X_USER_ACCESS_TOKEN),x402:Boolean(process.env.X402_PAY_TO)});
    if(req.method==="GET"&&path==="/.well-known/feedify.json")return send(res,200,{protocol:"feedify/1",name:"Feedify",thesis:"Compile a stream of information once, then turn it into many products.",services:{app:"https://feedify.dev",x:"https://x.feedify.dev",git:"https://git.feedify.dev",api:publicBase,mcp:`${mcpBase}/mcp`,x402:x402Base},formats:["feedify","rss2","json-feed-1.1","x-bot","webhook","blog","report","mcp","x402"]});
    if(req.method==="GET"&&path==="/v1/templates")return send(res,200,{templates});
    if(req.method==="GET"&&path==="/v1/products/catalog")return send(res,200,{outputs:OUTPUT_CATALOG});
    if(req.method==="GET"&&path==="/v1/home")return send(res,200,{items:await repo.home(uid)});
    if(req.method==="GET"&&path==="/v1/feeds")return send(res,200,{feeds:await repo.listFeeds(uid)});

    if(req.method==="POST"&&path==="/v1/feeds/compile"){
      const b=await body(req);if(!b.prompt)return send(res,400,{error:"prompt required"});
      return send(res,200,{program:await compileFeedPrompt(ai,String(b.prompt))});
    }
    if(req.method==="POST"&&path==="/v1/feeds"){
      const b=await body(req);if(!b.name||!b.objective)return send(res,400,{error:"name and objective required"});
      const program=b.program||await compileFeedPrompt(ai,String(b.objective));const now=new Date().toISOString();
      const f:Feed={id:stableId("feed",uid,String(b.name),now),slug:slugify(b.slug||b.name),creatorId:uid,creatorName:b.creatorName||"You",name:String(b.name),description:String(b.description||b.objective),emoji:String(b.emoji||"✦"),visibility:b.visibility||"public",version:1,program,sources:Array.isArray(b.sources)?b.sources:[],subscriberCount:0,subscribed:true,createdAt:now,updatedAt:now};
      await repo.saveFeed(f);await repo.subscribe(uid,f.id,true);return send(res,201,{feed:f,manifest:await manifestFor(f)});
    }

    const feedMatch=path.match(/^\/v1\/feeds\/([^/]+)$/);
    if(req.method==="GET"&&feedMatch){const f=await repo.getFeed(feedMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});return send(res,200,{feed:f,items:await repo.itemsForFeed(f.id)});}
    const latestMatch=path.match(/^\/v1\/feeds\/([^/]+)\/latest$/);
    if(req.method==="GET"&&latestMatch){const f=await repo.getFeed(latestMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});return send(res,200,{feed:f,item:(await repo.itemsForFeed(f.id,1))[0]||null});}
    const manifestMatch=path.match(/^\/v1\/feeds\/([^/]+)\/manifest$/);
    if(req.method==="GET"&&manifestMatch){const f=await repo.getFeed(manifestMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});return send(res,200,{manifest:await manifestFor(f)});}
    const chainMatch=path.match(/^\/v1\/feeds\/([^/]+)\/chain$/);
    if(req.method==="GET"&&chainMatch){const f=await repo.getFeed(chainMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});const outputs=await repo.outputsForFeed(f.id);return send(res,200,{feed:f.id,nodes:[...f.sources.map((s)=>({id:`source:${s.id}`,kind:"source",type:s.type,label:s.label||s.type})),{id:`feed:${f.id}`,kind:"feed",label:f.name},...outputs.map((o)=>({id:`output:${o.id}`,kind:"product",type:o.type,label:o.name,enabled:o.enabled}))],edges:[...f.sources.map((s)=>({from:`source:${s.id}`,to:`feed:${f.id}`})),...outputs.map((o)=>({from:`feed:${f.id}`,to:`output:${o.id}`}))]});}

    const runMatch=path.match(/^\/v1\/feeds\/([^/]+)\/run$/);
    if(req.method==="POST"&&runMatch){
      const b=await body(req);const f=await repo.getFeed(runMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});const prior=await repo.itemsForFeed(f.id,200);
      const items=await runFeed({feed:f,priorItems:prior,ai,env:{getxApiKey:process.env.GETX_API_KEY,getxBaseUrl:process.env.GETX_BASE_URL,githubToken:process.env.GITHUB_TOKEN,githubBaseUrl:process.env.GITHUB_BASE_URL}});await repo.saveItems(items);
      const deliveries=b.publish===true?await dispatch(f,items):[];return send(res,200,{items,created:items.length,deliveries});
    }

    const productsMatch=path.match(/^\/v1\/feeds\/([^/]+)\/products$/);
    if(req.method==="GET"&&productsMatch){const f=await repo.getFeed(productsMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});const outputs=await repo.outputsForFeed(f.id);return send(res,200,{outputs:outputs.map((o)=>({...o,config:outputPublicConfig(o)})),catalog:OUTPUT_CATALOG});}
    if(req.method==="POST"&&productsMatch){
      const b=await body(req);const f=await repo.getFeed(productsMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});const type=String(b.type||"") as OutputType;
      if(!OUTPUT_CATALOG.some((x)=>x.type===type))return send(res,400,{error:"unknown output type",allowed:OUTPUT_CATALOG.map((x)=>x.type)});
      const now=new Date().toISOString();const name=String(b.name||outputName(type));const output:OutputChannel={id:String(b.id||stableId("output",f.id,type,name)),feedId:f.id,type,name,enabled:b.enabled!==false,config:typeof b.config==="object"&&b.config?b.config:{},createdAt:now,updatedAt:now};
      await repo.saveOutput(output);return send(res,201,{output:{...output,config:outputPublicConfig(output)},manifest:await manifestFor(f)});
    }
    const outputPublish=path.match(/^\/v1\/feeds\/([^/]+)\/products\/([^/]+)\/publish$/);
    if(req.method==="POST"&&outputPublish){const f=await repo.getFeed(outputPublish[1],uid);const out=await repo.getOutput(outputPublish[2]);if(!f||!out||out.feedId!==f.id)return send(res,404,{error:"feed/output not found"});const items=await repo.itemsForFeed(f.id,20);const item=items.find((x)=>!(x.publishedOutputs||[]).includes(out.id));if(!item)return send(res,409,{error:"nothing unpublished"});const deliveries=await dispatchOutput({feed:f,items:[item],output:out,allFeedItems:items,env:process.env});for(const d of deliveries){await repo.recordDelivery(d);if(d.status==="success"&&d.itemId)await repo.markPublished(d.itemId,out.id);}return send(res,200,{deliveries});}
    const deliveryMatch=path.match(/^\/v1\/feeds\/([^/]+)\/deliveries$/);
    if(req.method==="GET"&&deliveryMatch){const f=await repo.getFeed(deliveryMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});return send(res,200,{deliveries:await repo.recentDeliveries(f.id)});}

    const subMatch=path.match(/^\/v1\/feeds\/([^/]+)\/subscribe$/);
    if(req.method==="POST"&&subMatch){const b=await body(req);const f=await repo.getFeed(subMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});await repo.subscribe(uid,f.id,b.subscribed!==false);return send(res,200,{ok:true,subscribed:b.subscribed!==false});}
    const repostMatch=path.match(/^\/v1\/items\/([^/]+)\/repost$/);
    if(req.method==="POST"&&repostMatch){const b=await body(req);return send(res,201,{repost:await repo.repost(uid,b.userName||"You",repostMatch[1],b.comment)});}
    const feedbackMatch=path.match(/^\/v1\/items\/([^/]+)\/feedback$/);
    if(req.method==="POST"&&feedbackMatch){const b=await body(req);await repo.feedback(uid,feedbackMatch[1],b.value as FeedbackValue);return send(res,200,{ok:true});}

    // Backwards-compatible one-click X publishing. Internally this now uses the same product-chain dispatcher as every other output.
    const publishMatch=path.match(/^\/v1\/feeds\/([^/]+)\/publish\/x$/);
    if(req.method==="POST"&&publishMatch){const f=await repo.getFeed(publishMatch[1],uid);if(!f)return send(res,404,{error:"feed not found"});let out=(await repo.outputsForFeed(f.id)).find((x)=>x.type==="x_bot");if(!out){const now=new Date().toISOString();out={id:stableId("output",f.id,"x_bot"),feedId:f.id,type:"x_bot",name:"X bot",enabled:true,config:{strategy:"smart"},createdAt:now,updatedAt:now};await repo.saveOutput(out);}const items=await repo.itemsForFeed(f.id,20);const item=items.find((x)=>!(x.publishedOutputs||[]).includes(out!.id));if(!item)return send(res,409,{error:"nothing unpublished"});const deliveries=await dispatchOutput({feed:f,items:[item],output:out,allFeedItems:items,env:process.env});for(const d of deliveries)await repo.recordDelivery(d);return send(res,200,{ok:true,deliveries,itemId:item.id});}

    const publicMatch=path.match(/^\/f\/([^/]+)(?:\/(rss\.xml|feed\.json|report\.md|manifest\.json))?$/);
    if(req.method==="GET"&&publicMatch){const f=await repo.getFeed(publicMatch[1],uid);if(!f||f.visibility==="private")return send(res,404,{error:"feed not found"});const items=await repo.itemsForFeed(f.id,50);const format=publicMatch[2];if(format==="rss.xml")return send(res,200,toRss(f,items,publicBase),"application/rss+xml; charset=utf-8");if(format==="feed.json")return send(res,200,toJsonFeed(f,items,publicBase),"application/feed+json; charset=utf-8");if(format==="report.md")return send(res,200,toMarkdownReport(f,items),"text/markdown; charset=utf-8");if(format==="manifest.json")return send(res,200,await manifestFor(f));return send(res,200,toPublicHtml(f,items),"text/html; charset=utf-8");}

    return send(res,404,{error:"not found",path});
  }catch(error:any){console.error(error);return send(res,500,{error:error?.message||"internal error"});}
});
server.listen(port,"0.0.0.0",()=>console.log(`Feedify API → http://localhost:${port}`));
