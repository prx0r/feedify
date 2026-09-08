-- Production schema for Feedify. The MVP uses local JSON persistence by default.
create extension if not exists pgcrypto;

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  handle text unique not null,
  display_name text not null,
  avatar_url text,
  created_at timestamptz not null default now()
);

create table feeds (
  id uuid primary key default gen_random_uuid(),
  creator_id uuid not null references profiles(id) on delete cascade,
  slug text unique not null,
  name text not null,
  description text not null default '',
  emoji text not null default '✦',
  visibility text not null check (visibility in ('private','unlisted','public')) default 'public',
  current_version int not null default 1,
  subscriber_count bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table feed_versions (
  feed_id uuid not null references feeds(id) on delete cascade,
  version int not null,
  objective text not null,
  program jsonb not null,
  created_at timestamptz not null default now(),
  primary key(feed_id,version)
);

create table feed_sources (
  id uuid primary key default gen_random_uuid(),
  feed_id uuid not null references feeds(id) on delete cascade,
  feed_version int not null,
  source_type text not null,
  config jsonb not null,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  foreign key(feed_id,feed_version) references feed_versions(feed_id,version) on delete cascade
);

create table feed_items (
  id uuid primary key default gen_random_uuid(),
  feed_id uuid not null references feeds(id) on delete cascade,
  feed_version int not null,
  kind text not null check(kind in ('source','summary','synthesis','generated')),
  title text,
  body text not null,
  canonical_url text,
  score jsonb,
  published_outputs text[] not null default '{}',
  created_at timestamptz not null default now(),
  foreign key(feed_id,feed_version) references feed_versions(feed_id,version)
);

create index feed_items_feed_created_idx on feed_items(feed_id,created_at desc);

create table provenance (
  id bigint generated always as identity primary key,
  feed_item_id uuid not null references feed_items(id) on delete cascade,
  source_id uuid references feed_sources(id) on delete set null,
  source_type text not null,
  source_label text,
  source_url text,
  source_item_id text,
  excerpt text
);

create table subscriptions (
  user_id uuid not null references profiles(id) on delete cascade,
  feed_id uuid not null references feeds(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(user_id,feed_id)
);

create table reposts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  feed_item_id uuid not null references feed_items(id) on delete cascade,
  comment text,
  created_at timestamptz not null default now()
);

create table item_feedback (
  user_id uuid not null references profiles(id) on delete cascade,
  feed_item_id uuid not null references feed_items(id) on delete cascade,
  value text not null check(value in ('useful','very_useful','already_knew','noise','too_late','actioned')),
  created_at timestamptz not null default now(),
  primary key(user_id,feed_item_id)
);

create table output_channels (
  id uuid primary key default gen_random_uuid(),
  feed_id uuid not null references feeds(id) on delete cascade,
  output_type text not null,
  encrypted_config jsonb not null default '{}',
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);

alter table feeds enable row level security;
alter table subscriptions enable row level security;
alter table reposts enable row level security;
alter table item_feedback enable row level security;

create policy "public feeds readable" on feeds for select using (visibility='public' or creator_id=auth.uid());
create policy "creators manage feeds" on feeds for all using (creator_id=auth.uid()) with check (creator_id=auth.uid());
create policy "own subscriptions" on subscriptions for all using (user_id=auth.uid()) with check (user_id=auth.uid());
create policy "own reposts" on reposts for all using (user_id=auth.uid()) with check (user_id=auth.uid());
create policy "own feedback" on item_feedback for all using (user_id=auth.uid()) with check (user_id=auth.uid());
