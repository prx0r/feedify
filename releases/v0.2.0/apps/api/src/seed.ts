import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { seedDatabase } from "./seed-data.ts";
const file=resolve(process.env.DATA_FILE || "./data/feedify.json");
await mkdir(dirname(file),{recursive:true});
await writeFile(file,JSON.stringify(seedDatabase,null,2));
console.log(`Seeded ${seedDatabase.feeds.length} feeds and ${seedDatabase.items.length} items → ${file}`);
