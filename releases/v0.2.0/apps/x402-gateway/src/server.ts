import express from "express";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { FeedifyClient } from "@feedify/sdk";

const port=Number(process.env.PORT||8790);
const api=new FeedifyClient(process.env.FEEDIFY_API_URL||"http://localhost:8787");
const facilitatorUrl=process.env.X402_FACILITATOR_URL||"https://x402.org/facilitator";
const defaultPayTo=process.env.X402_PAY_TO||"";
const defaultNetwork=(process.env.X402_NETWORK||"eip155:8453") as `${string}:${string}`;
const facilitator=new HTTPFacilitatorClient({url:facilitatorUrl});
const resourceServer=new x402ResourceServer(facilitator);
const feeds=await api.feeds();
const routes:Record<string,any>={};
const paid=new Map<string,{slug:string;price:string;network:string;payTo:string}>();
const networks=new Set<string>();

for(const feed of feeds){
  const outputs=await api.products(feed.id);
  const x=outputs.find((o)=>o.type==="x402"&&o.enabled);if(!x)continue;
  const price=String(x.config.price||"$0.01");const network=String(x.config.network||defaultNetwork);const payTo=String(x.config.payTo||defaultPayTo);
  if(!payTo){console.warn(`Skipping ${feed.slug}: x402 payTo not configured`);continue;}
  const path=`/paid/${feed.slug}/latest`;routes[`GET ${path}`]={accepts:{scheme:"exact",price,network,payTo,maxTimeoutSeconds:120},description:`Latest high-signal item from ${feed.name}`};
  paid.set(feed.slug,{slug:feed.slug,price,network,payTo});networks.add(network);
}
for(const network of networks)resourceServer.register(network as any,new ExactEvmScheme());

const app=express();
app.get("/health",(_req,res)=>res.json({ok:true,service:"feedify-x402",feeds:paid.size,facilitator:facilitatorUrl}));
app.get("/catalog",async(_req,res)=>res.json({protocol:"feedify-x402/1",feeds:[...paid.values()].map((p)=>({...p,url:`/paid/${p.slug}/latest`}))}));
if(Object.keys(routes).length)app.use(paymentMiddleware(routes as any,resourceServer));
app.get("/paid/:slug/latest",async(req,res,next)=>{try{if(!paid.has(req.params.slug))return res.status(404).json({error:"paid feed not found"});const result=await api.latest(req.params.slug);return res.json({protocol:"feedify-paid-item/1",feed:result.feed,item:result.item});}catch(e){next(e);}});
app.listen(port,"0.0.0.0",()=>console.log(`Feedify x402 gateway → http://localhost:${port} (${paid.size} paid feeds)`));
