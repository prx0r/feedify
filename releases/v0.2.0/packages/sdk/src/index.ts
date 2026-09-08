import type { Feed, FeedItem, FeedProductManifest, OutputChannel } from "@feedify/core";

export class FeedifyClient{
  readonly baseUrl:string;
  constructor(baseUrl="http://localhost:8787",private readonly headers:Record<string,string>={}){this.baseUrl=baseUrl.replace(/\/$/,"");}
  private async get<T>(path:string):Promise<T>{const res=await fetch(`${this.baseUrl}${path}`,{headers:{accept:"application/json",...this.headers}});if(!res.ok)throw new Error(`Feedify ${res.status}: ${await res.text()}`);return res.json() as Promise<T>;}
  async feeds(){return (await this.get<{feeds:Feed[]}>("/v1/feeds")).feeds;}
  async feed(id:string){return this.get<{feed:Feed;items:FeedItem[]}>(`/v1/feeds/${encodeURIComponent(id)}`);}
  async latest(id:string){return this.get<{feed:Feed;item:FeedItem|null}>(`/v1/feeds/${encodeURIComponent(id)}/latest`);}
  async products(id:string){return (await this.get<{outputs:OutputChannel[]}>(`/v1/feeds/${encodeURIComponent(id)}/products`)).outputs;}
  async manifest(id:string){return (await this.get<{manifest:FeedProductManifest}>(`/v1/feeds/${encodeURIComponent(id)}/manifest`)).manifest;}
}
