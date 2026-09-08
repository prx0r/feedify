-- Feedify 0.2: a feed compiles once, then fans out into products.
-- Extends the original output_channels table instead of introducing parallel output models.
alter table output_channels add column if not exists display_name text;
alter table output_channels add column if not exists updated_at timestamptz not null default now();

create table if not exists output_deliveries (
  id uuid primary key default gen_random_uuid(),
  output_id uuid not null references output_channels(id) on delete cascade,
  feed_id uuid not null references feeds(id) on delete cascade,
  feed_item_id uuid references feed_items(id) on delete set null,
  status text not null check(status in ('success','failed','dry_run')),
  external_id text,
  detail text,
  created_at timestamptz not null default now()
);
create index if not exists output_deliveries_feed_created_idx on output_deliveries(feed_id,created_at desc);
create index if not exists output_deliveries_output_created_idx on output_deliveries(output_id,created_at desc);

-- Public output metadata is readable with the public feed. Secrets remain inside encrypted_config.
alter table output_channels enable row level security;
alter table output_deliveries enable row level security;
create policy "public output metadata readable" on output_channels for select using (
  exists(select 1 from feeds f where f.id=output_channels.feed_id and (f.visibility='public' or f.creator_id=auth.uid()))
);
create policy "creators manage outputs" on output_channels for all using (
  exists(select 1 from feeds f where f.id=output_channels.feed_id and f.creator_id=auth.uid())
) with check (
  exists(select 1 from feeds f where f.id=output_channels.feed_id and f.creator_id=auth.uid())
);
create policy "creators read deliveries" on output_deliveries for select using (
  exists(select 1 from feeds f where f.id=output_deliveries.feed_id and f.creator_id=auth.uid())
);
