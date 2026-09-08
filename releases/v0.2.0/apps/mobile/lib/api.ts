import type { Feed, FeedItem, FeedProgram, FeedSource, FeedbackValue, OutputChannel, OutputType, FeedProductManifest } from "@feedify/core";
import { demoFeeds, demoItems } from "./demo";
const BASE=(process.env.EXPO_PUBLIC_API_URL||"http://localhost:8787").replace(/\/$/,"");
async function request<T>(path:string,init?:RequestInit):Promise<T>{const res=await fetch(`${BASE}${path}`,{...init,headers:{"content-type":"application/json","x-feedify-user":"demo",...(init?.headers||{})}});if(!res.ok)throw new Error(`${res.status}: ${await res.text()}`);return res.json();}
export async function home():Promise<FeedItem[]>{try{return(await request<{items:FeedItem[]}>("/v1/home")).items}catch{return demoItems}}
export async function feeds():Promise<Feed[]>{try{return(await request<{feeds:Feed[]}>("/v1/feeds")).feeds}catch{return demoFeeds}}
export async function feed(id:string):Promise<{feed:Feed;items:FeedItem[]}>{try{return await request(`/v1/feeds/${id}`)}catch{const f=demoFeeds.find((x)=>x.id===id||x.slug===id)||demoFeeds[0];return{feed:f,items:demoItems.filter((x)=>x.feedId===f.id)}}}
export async function compile(prompt:string):Promise<FeedProgram>{return(await request<{program:FeedProgram}>("/v1/feeds/compile",{method:"POST",body:JSON.stringify({prompt})})).program}
export async function createFeed(input:{name:string;objective:string;description?:string;emoji?:string;program?:FeedProgram;sources?:FeedSource[]}):Promise<Feed>{return(await request<{feed:Feed}>("/v1/feeds",{method:"POST",body:JSON.stringify(input)})).feed}
export async function subscribe(id:string,subscribed:boolean){return request(`/v1/feeds/${id}/subscribe`,{method:"POST",body:JSON.stringify({subscribed})})}
export async function repost(id:string,comment?:string){return request(`/v1/items/${id}/repost`,{method:"POST",body:JSON.stringify({userName:"You",comment})})}
export async function feedback(id:string,value:FeedbackValue){return request(`/v1/items/${id}/feedback`,{method:"POST",body:JSON.stringify({value})})}

export async function products(id:string):Promise<OutputChannel[]>{return(await request<{outputs:OutputChannel[]}>(`/v1/feeds/${id}/products`)).outputs}
export async function addProduct(id:string,input:{type:OutputType;name?:string;enabled?:boolean;config?:Record<string,unknown>}):Promise<OutputChannel>{return(await request<{output:OutputChannel}>(`/v1/feeds/${id}/products`,{method:"POST",body:JSON.stringify(input)})).output}
export async function manifest(id:string):Promise<FeedProductManifest>{return(await request<{manifest:FeedProductManifest}>(`/v1/feeds/${id}/manifest`)).manifest}
export async function run(id:string,publish=false){return request(`/v1/feeds/${id}/run`,{method:"POST",body:JSON.stringify({publish})})}
