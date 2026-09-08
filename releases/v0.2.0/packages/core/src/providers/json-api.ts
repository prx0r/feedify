import type { Candidate, FeedSource } from "../types.ts";
import { stableId } from "../utils.ts";

type JsonSource = Extract<FeedSource,{type:"json_api"}>;

function at(obj:any,path?:string){if(!path)return obj;return path.split(".").filter(Boolean).reduce((v,k)=>v?.[k],obj);}
function field(obj:any,name?:string){return name?at(obj,name):undefined;}

export async function fetchJsonApi(source:JsonSource):Promise<Candidate[]>{
  const res=await fetch(source.url,{headers:{accept:"application/json","user-agent":"Feedify/0.2 (+https://feedify.dev)"},signal:AbortSignal.timeout(12000)});
  if(!res.ok)throw new Error(`JSON source ${res.status}: ${source.url}`);
  const root=await res.json();const raw=at(root,source.itemsPath);const items=Array.isArray(raw)?raw:Array.isArray(root)?root:[];
  return items.slice(0,50).map((item:any,index:number)=>{
    const title=String(field(item,source.titleField||"title")||"");
    const text=String(field(item,source.textField||"text")||field(item,"description")||field(item,"content")||title);
    const url=field(item,source.urlField||"url");const author=field(item,source.authorField||"author");const publishedAt=field(item,source.dateField||"published_at")||field(item,"created_at");
    const ext=String(field(item,"id")||url||`${title}:${index}`);
    return {id:stableId(source.id,ext),sourceId:source.id,sourceType:"json_api" as const,sourceLabel:source.label,title:title||undefined,text,url:url?String(url):undefined,author:author?String(author):undefined,publishedAt:publishedAt?String(publishedAt):undefined,metadata:{raw:item}};
  }).filter((x:any)=>x.text);
}
