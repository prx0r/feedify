# API examples

## Compile a natural-language feed

```bash
curl -s http://localhost:8787/v1/feeds/compile \
  -H 'content-type: application/json' \
  -d '{"prompt":"Distill the Tantraloka into one surprising daily insight. Avoid generic spirituality."}'
```

## Create it

```bash
curl -s http://localhost:8787/v1/feeds \
  -H 'content-type: application/json' \
  -d '{
    "name":"Tantraloka Daily",
    "objective":"Distill the Tantraloka into one surprising daily insight.",
    "emoji":"◉",
    "sources":[{
      "id":"tantra-corpus",
      "type":"corpus",
      "label":"My source corpus",
      "items":[{"id":"1","text":"Paste or ingest source-grounded chunks here."}]
    }]
  }'
```

## Run a feed now

```bash
curl -X POST http://localhost:8787/v1/feeds/tantraloka-daily/run
```

## Subscribe

```bash
curl -X POST http://localhost:8787/v1/feeds/feed_tantraloka/subscribe \
  -H 'content-type: application/json' \
  -d '{"subscribed":true}'
```

## Export

```bash
curl http://localhost:8787/f/tantraloka-daily/rss.xml
curl http://localhost:8787/f/tantraloka-daily/feed.json
curl http://localhost:8787/f/tantraloka-daily/report.md
```
