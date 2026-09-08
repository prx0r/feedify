import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import type { DatabaseShape, Feed, FeedItem, FeedbackValue, OutputChannel, OutputDelivery, Repost } from "@feedify/core";
import { defaultOutputs, stableId } from "@feedify/core";

const EMPTY: DatabaseShape = { feeds: [], items: [], subscriptions: [], reposts: [], feedback: [], outputs: [], deliveries: [] };

export class JsonRepository {
  constructor(private readonly file: string) {}

  private async read(): Promise<DatabaseShape> {
    try {
      const parsed=JSON.parse(await readFile(this.file, "utf8"));
      return {...structuredClone(EMPTY),...parsed,outputs:Array.isArray(parsed.outputs)?parsed.outputs:[],deliveries:Array.isArray(parsed.deliveries)?parsed.deliveries:[]};
    } catch { return structuredClone(EMPTY); }
  }

  private async write(db: DatabaseShape) {
    await mkdir(dirname(this.file), { recursive: true });
    const tmp = `${this.file}.tmp`;
    await writeFile(tmp, JSON.stringify(db, null, 2));
    await rename(tmp, this.file);
  }

  async listFeeds(userId = "demo") { const db = await this.read(); return db.feeds.map((f) => ({...f, subscribed: db.subscriptions.some((s) => s.userId === userId && s.feedId === f.id)})); }
  async getFeed(idOrSlug: string, userId = "demo") { return (await this.listFeeds(userId)).find((f) => f.id === idOrSlug || f.slug === idOrSlug); }
  async saveFeed(feed: Feed) { const db = await this.read(); const i=db.feeds.findIndex((x)=>x.id===feed.id); if(i>=0)db.feeds[i]=feed; else {db.feeds.push(feed);db.outputs.push(...defaultOutputs(feed).filter(o=>!db.outputs.some(x=>x.id===o.id)));} await this.write(db); return feed; }
  async itemsForFeed(feedId: string, limit=50) { const db=await this.read(); return db.items.filter((x)=>x.feedId===feedId).sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).slice(0,limit); }
  async home(userId="demo", limit=80) { const db=await this.read(); const ids=new Set(db.subscriptions.filter((s)=>s.userId===userId).map((s)=>s.feedId)); return db.items.filter((x)=>ids.has(x.feedId)).sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).slice(0,limit); }
  async saveItems(items: FeedItem[]) { const db=await this.read(); for(const item of items){if(!db.items.some((x)=>x.id===item.id))db.items.push(item);} await this.write(db); }
  async subscribe(userId:string, feedId:string, subscribed:boolean) { const db=await this.read(); const wasSubscribed=db.subscriptions.some((s)=>s.userId===userId&&s.feedId===feedId); db.subscriptions=db.subscriptions.filter((s)=>!(s.userId===userId&&s.feedId===feedId)); if(subscribed) db.subscriptions.push({userId,feedId,createdAt:new Date().toISOString()}); const feed=db.feeds.find((x)=>x.id===feedId); if(feed && wasSubscribed!==subscribed){feed.subscriberCount=Math.max(0,feed.subscriberCount+(subscribed?1:-1));} await this.write(db); }
  async repost(userId:string,userName:string,itemId:string,comment?:string):Promise<Repost>{const db=await this.read();const repost={id:stableId("repost",userId,itemId,comment||""),userId,userName,feedItemId:itemId,comment,createdAt:new Date().toISOString()};if(!db.reposts.some((x)=>x.id===repost.id)){db.reposts.push(repost);const item=db.items.find((x)=>x.id===itemId);if(item)item.repostCount++;}await this.write(db);return repost;}
  async feedback(userId:string,itemId:string,value:FeedbackValue){const db=await this.read();db.feedback=db.feedback.filter((x)=>!(x.userId===userId&&x.feedItemId===itemId));db.feedback.push({id:stableId("feedback",userId,itemId),userId,feedItemId:itemId,value,createdAt:new Date().toISOString()});await this.write(db);}
  async markPublished(itemId:string, output:string){const db=await this.read();const item=db.items.find((x)=>x.id===itemId);if(item){item.publishedOutputs=[...new Set([...(item.publishedOutputs||[]),output])];await this.write(db);} }
  async outputsForFeed(feedId:string){const db=await this.read();return db.outputs.filter((x)=>x.feedId===feedId);}
  async allEnabledOutputs(){const db=await this.read();return db.outputs.filter((x)=>x.enabled);}
  async saveOutput(output:OutputChannel){const db=await this.read();const i=db.outputs.findIndex((x)=>x.id===output.id);if(i>=0)db.outputs[i]=output;else db.outputs.push(output);await this.write(db);return output;}
  async getOutput(id:string){const db=await this.read();return db.outputs.find((x)=>x.id===id);}
  async recordDelivery(delivery:OutputDelivery){const db=await this.read();if(!db.deliveries.some((x)=>x.id===delivery.id))db.deliveries.push(delivery);await this.write(db);return delivery;}
  async recentDeliveries(feedId:string,limit=30){const db=await this.read();return db.deliveries.filter((x)=>x.feedId===feedId).sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).slice(0,limit);}
}
