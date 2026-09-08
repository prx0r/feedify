export type FeedMode = "curate" | "distill" | "synthesize" | "generate";

export type FeedSource =
  | { id: string; type: "rss"; url: string; label?: string }
  | { id: string; type: "url"; url: string; label?: string }
  | { id: string; type: "x_search"; query: string; product?: "Latest" | "Top"; label?: string }
  | { id: string; type: "github_search"; query: string; label?: string; sort?: "updated" | "stars"; order?: "asc" | "desc" }
  | { id: string; type: "json_api"; url: string; label?: string; itemsPath?: string; titleField?: string; textField?: string; urlField?: string; authorField?: string; dateField?: string }
  | { id: string; type: "corpus"; label: string; items: CorpusEntry[] };

export type CorpusEntry = {
  id: string;
  title?: string;
  text: string;
  url?: string;
  citation?: string;
};

export type FeedProgram = {
  objective: string;
  mode: FeedMode;
  include: string[];
  exclude: string[];
  rankFor: string[];
  voice?: string;
  maxItemsPerRun: number;
  minScore: number;
  sourceStrictness: number;
  noveltyWeight: number;
};

export type Feed = {
  id: string;
  slug: string;
  creatorId: string;
  creatorName: string;
  name: string;
  description: string;
  emoji: string;
  visibility: "private" | "unlisted" | "public";
  version: number;
  program: FeedProgram;
  sources: FeedSource[];
  subscriberCount: number;
  subscribed?: boolean;
  createdAt: string;
  updatedAt: string;
};

export type Provenance = {
  sourceId: string;
  sourceType: FeedSource["type"];
  sourceLabel?: string;
  sourceUrl?: string;
  sourceItemId?: string;
  excerpt?: string;
};

export type Candidate = {
  id: string;
  sourceId: string;
  sourceType: FeedSource["type"];
  sourceLabel?: string;
  title?: string;
  text: string;
  url?: string;
  author?: string;
  publishedAt?: string;
  engagement?: number;
  metadata?: Record<string, unknown>;
};

export type ScoreBreakdown = {
  relevance: number;
  novelty: number;
  quality: number;
  actionability: number;
  total: number;
};

export type FeedItem = {
  id: string;
  feedId: string;
  feedSlug: string;
  feedName: string;
  feedEmoji: string;
  feedVersion: number;
  kind: "source" | "summary" | "synthesis" | "generated";
  title?: string;
  body: string;
  canonicalUrl?: string;
  provenance: Provenance[];
  scores?: ScoreBreakdown;
  createdAt: string;
  repostCount: number;
  likeCount: number;
  commentCount: number;
  publishedOutputs?: string[];
};

export type Repost = {
  id: string;
  userId: string;
  userName: string;
  feedItemId: string;
  comment?: string;
  createdAt: string;
};

export type FeedbackValue = "useful" | "very_useful" | "already_knew" | "noise" | "too_late" | "actioned";

export type UserFeedback = {
  id: string;
  userId: string;
  feedItemId: string;
  value: FeedbackValue;
  createdAt: string;
};

export type OutputType =
  | "feedify"
  | "public_web"
  | "rss"
  | "json_feed"
  | "x_bot"
  | "webhook"
  | "blog"
  | "report"
  | "x402"
  | "mcp";

export type OutputChannel = {
  id: string;
  feedId: string;
  type: OutputType;
  name: string;
  enabled: boolean;
  config: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

export type OutputDelivery = {
  id: string;
  outputId: string;
  feedId: string;
  itemId?: string;
  status: "success" | "failed" | "dry_run";
  externalId?: string;
  detail?: string;
  createdAt: string;
};

export type FeedProductManifest = {
  protocol: "feedify/1";
  feed: Pick<Feed, "id" | "slug" | "name" | "description" | "emoji" | "version">;
  canonical: string;
  endpoints: {
    api: string;
    web: string;
    rss: string;
    jsonFeed: string;
    report: string;
    mcp: string;
  };
  outputs: Array<{
    id: string;
    type: OutputType;
    name: string;
    enabled: boolean;
    href?: string;
    price?: string;
    network?: string;
  }>;
};

export type DatabaseShape = {
  feeds: Feed[];
  items: FeedItem[];
  subscriptions: { userId: string; feedId: string; createdAt: string }[];
  reposts: Repost[];
  feedback: UserFeedback[];
  outputs: OutputChannel[];
  deliveries: OutputDelivery[];
};
