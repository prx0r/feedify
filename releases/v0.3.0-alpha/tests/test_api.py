from fastapi.testclient import TestClient

from fish.api import app


def test_product_flow():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["feeds"] >= 5
        assert health.json()["signals"] >= 5

        feeds = client.get("/api/feeds").json()
        assert any(f["slug"] == "agent-commerce-alpha" for f in feeds)

        created = client.post(
            "/api/feeds",
            json={
                "name": "Test Alpha",
                "prompt": "Only new buildable iOS and agent opportunities, high signal, less noise",
                "icon": "T",
            },
        )
        assert created.status_code == 200
        slug = created.json()["slug"]

        feed = client.get(f"/api/feeds/{slug}")
        assert feed.status_code == 200
        assert feed.json()["feed"]["name"] == "Test Alpha"

        json_feed = client.get(f"/api/feeds/{slug}.json")
        assert json_feed.status_code == 200
        assert "items" in json_feed.json()

        rss = client.get(f"/api/feeds/{slug}.rss")
        assert rss.status_code == 200
        assert "<rss" in rss.text

        manifest = client.get(f"/manifest/{slug}.webmanifest")
        assert manifest.status_code == 200
        assert manifest.json()["name"] == "Test Alpha"

        icon = client.get(f"/icon/{slug}/192.png")
        assert icon.status_code == 200
        assert icon.headers["content-type"].startswith("image/png")
        assert len(icon.content) > 100

        page = client.get(f"/f/{slug}")
        assert page.status_code == 200
        assert "apple-mobile-web-app-title" in page.text
        assert "Test Alpha" in page.text

        fork = client.post(f"/api/feeds/{slug}/fork", json={"name": "Forked Alpha"})
        assert fork.status_code == 200
        assert fork.json()["slug"].startswith("forked-alpha")


def test_sources_endpoint():
    with TestClient(app) as client:
        sources = client.get("/api/sources")
        assert sources.status_code == 200
        names = {s["name"] for s in sources.json()}
        assert {"trustmrr", "glama", "github", "hackernews", "storeleads", "appfigures"}.issubset(names)
