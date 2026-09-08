import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { OUTPUT_CATALOG, buildFeedManifest, defaultOutputs, stableId } from "../packages/core/src/index.ts";

function normalize(s){return s.toLowerCase().replace(/https?:\/\/\S+/g,"").replace(/[^a-z0-9\s]/g," ").replace(/\s+/g," ").trim()}
function jaccard(a,b){const A=new Set(normalize(a).split(" ").filter(x=>x.length>2)),B=new Set(normalize(b).split(" ").filter(x=>x.length>2));let i=0;for(const x of A)if(B.has(x))i++;return i/(A.size+B.size-i||1)}
assert.equal(stableId("a","b"),stableId("a","b"));assert.notEqual(stableId("a","b"),stableId("a","c"));
assert.ok(jaccard("new shopify agent api","shopify launches new agent api")>.4);
assert.ok(jaccard("tantraloka recognition consciousness","new github MCP server")<.2);
assert.ok(OUTPUT_CATALOG.some(x=>x.type==="x402"));assert.ok(OUTPUT_CATALOG.some(x=>x.type==="x_bot"));assert.ok(OUTPUT_CATALOG.some(x=>x.type==="mcp"));
const feed={id:"f",slug:"signal",creatorId:"u",creatorName:"u",name:"Signal",description:"Signal",emoji:"✦",visibility:"public",version:1,program:{objective:"signal",mode:"curate",include:[],exclude:[],rankFor:[],maxItemsPerRun:5,minScore:.5,sourceStrictness:.8,noveltyWeight:.9},sources:[],subscriberCount:0,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()};
const outputs=defaultOutputs(feed);outputs.push({id:"paid",feedId:"f",type:"x402",name:"Paid API",enabled:true,config:{price:"$0.01",network:"eip155:8453"},createdAt:feed.createdAt,updatedAt:feed.updatedAt});
const manifest=buildFeedManifest(feed,outputs,"https://api.feedify.dev");assert.equal(manifest.protocol,"feedify/1");assert.equal(manifest.outputs.find(x=>x.type==="x402")?.price,"$0.01");
const readme=await readFile(new URL("../README.md",import.meta.url),"utf8");assert.match(readme,/Tantrāloka Daily/);assert.match(readme,/JSON Feed 1\.1/);assert.match(readme,/x402/i);
const sql=await readFile(new URL("../supabase/migrations/0001_filterfeed.sql",import.meta.url),"utf8");for(const table of ["feeds","feed_items","provenance","subscriptions","reposts","item_feedback"])assert.match(sql,new RegExp(`create table ${table}`));
const sql2=await readFile(new URL("../supabase/migrations/0002_product_chain.sql",import.meta.url),"utf8");assert.match(sql2,/output_deliveries/);
console.log("✓ Feedify 0.2 smoke tests passed");
