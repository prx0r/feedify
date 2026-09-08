import { createServer } from "node:http";
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { toNodeHandler } from "@modelcontextprotocol/node";
import * as z from "zod/v4";
import { FeedifyClient } from "@feedify/sdk";

const port=Number(process.env.PORT||8791);const api=new FeedifyClient(process.env.FEEDIFY_API_URL||"http://localhost:8787");
function jsonText(value:unknown){return {content:[{type:"text" as const,text:JSON.stringify(value,null,2)}]};}
function build(){
  const server=new McpServer({name:"feedify",version:"0.2.0"});
  server.registerTool("list_feeds",{description:"List public Feedify feeds available to agents"},async()=>jsonText(await api.feeds()));
  server.registerTool("get_feed",{description:"Get a Feedify feed definition and recent items",inputSchema:z.object({feed:z.string(),limit:z.number().int().min(1).max(50).default(10)})},async({feed,limit})=>{const x=await api.feed(feed);return jsonText({...x,items:x.items.slice(0,limit)});});
  server.registerTool("latest_signal",{description:"Get the latest signal from a Feedify feed",inputSchema:z.object({feed:z.string()})},async({feed})=>jsonText(await api.latest(feed)));
  server.registerTool("feed_manifest",{description:"Get machine-readable outputs and paid endpoint metadata for a Feedify feed",inputSchema:z.object({feed:z.string()})},async({feed})=>jsonText(await api.manifest(feed)));
  return server;
}
const handler=createMcpHandler(build);const nodeHandler=toNodeHandler(handler);
createServer((req,res)=>{if(req.url!=="/mcp") {res.writeHead(404);return res.end("not found");}void nodeHandler(req,res);}).listen(port,"0.0.0.0",()=>console.log(`Feedify MCP → http://localhost:${port}/mcp`));
