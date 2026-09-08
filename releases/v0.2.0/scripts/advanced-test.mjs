import assert from "node:assert/strict";
import { createServer } from "node:http";
import { fetchGitHub } from "../packages/core/src/providers/github.ts";
import { fetchJsonApi } from "../packages/core/src/providers/json-api.ts";
import { publishToX } from "../apps/api/src/x-publisher.ts";
import { dispatchOutput } from "../apps/api/src/output-dispatcher.ts";

const server=createServer((req,res)=>{
  res.setHeader("content-type","application/json");
  if(req.url?.startsWith("/search/repositories"))return res.end(JSON.stringify({items:[{id:123,full_name:"signal/repo",description:"New agent capability",html_url:"https://github.com/signal/repo",stargazers_count:99,forks_count:4,language:"TypeScript",updated_at:"2026-09-08T00:00:00Z",owner:{login:"signal"},topics:["agents"]}]}));
  if(req.url==="/json")return res.end(JSON.stringify({items:[{id:"a",headline:"Alpha",summary:"Important machine-readable signal",href:"https://example.com/a",who:"oracle",when:"2026-09-08T00:00:00Z"}]}));
  res.statusCode=404;res.end("{}");
});
await new Promise(r=>server.listen(0,"127.0.0.1",r));const address=server.address();const base=`http://127.0.0.1:${address.port}`;

const gh=await fetchGitHub({id:"g",type:"github_search",query:"agents",label:"Git"},{githubBaseUrl:base});
assert.equal(gh.length,1);assert.equal(gh[0].title,"signal/repo");assert.equal(gh[0].metadata?.stars,99);
const js=await fetchJsonApi({id:"j",type:"json_api",url:`${base}/json`,itemsPath:"items",titleField:"headline",textField:"summary",urlField:"href",authorField:"who",dateField:"when"});
assert.equal(js[0].title,"Alpha");assert.equal(js[0].author,"oracle");

const baseItem={id:"i",feedId:"f",feedSlug:"alpha",feedName:"Alpha",feedEmoji:"↗",feedVersion:1,title:"Signal",body:"A useful source item",canonicalUrl:"https://x.com/signal/status/123456789",provenance:[{sourceId:"x",sourceType:"x_search",sourceItemId:"123456789",sourceUrl:"https://x.com/signal/status/123456789"}],createdAt:new Date().toISOString(),repostCount:0,likeCount:0,commentCount:0};
const out={id:"o",feedId:"f",type:"x_bot",name:"bot",enabled:true,config:{strategy:"smart",dryRun:true},createdAt:baseItem.createdAt,updatedAt:baseItem.createdAt};
const sourceResult=await publishToX({...baseItem,kind:"source"},out,{});assert.equal(sourceResult.strategy,"repost");assert.equal(sourceResult.dryRun,true);
const transformed=await publishToX({...baseItem,kind:"summary"},out,{});assert.equal(transformed.strategy,"post");
const feed={id:"f",slug:"alpha",creatorId:"u",creatorName:"u",name:"Alpha",description:"",emoji:"↗",visibility:"public",version:1,program:{objective:"alpha",mode:"curate",include:[],exclude:[],rankFor:[],maxItemsPerRun:5,minScore:.5,sourceStrictness:.8,noveltyWeight:.9},sources:[],subscriberCount:0,createdAt:baseItem.createdAt,updatedAt:baseItem.createdAt};
const webhook={...out,id:"w",type:"webhook",name:"hook",config:{url:"https://example.com/hook",dryRun:true}};
const d=await dispatchOutput({feed,items:[{...baseItem,kind:"source"}],output:webhook,allFeedItems:[]});assert.equal(d[0].status,"dry_run");
server.close();
console.log("✓ Feedify providers + smart X + webhook tests passed");
