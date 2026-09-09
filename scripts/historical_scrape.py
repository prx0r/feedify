#!/usr/bin/env python3
"""
Historical Scrape for Priority 1 Accounts
Cost: ~$0.001 per API call
Target: Full 2-year history, no replies, high signal only
"""

import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

API_KEY = "get-x-api-0d101a57d43f429a69ff8dd821186eeb2f889406859be720"
BASE_URL = "https://api.getxapi.com/twitter/user/tweets"

# Priority 1 accounts with user IDs
ACCOUNTS = {
    "Tim_Dettmers": "872274950",
    "clattner_llvm": "2543588034",
    "ArjunNMurti": "319388951",
    "dylan522p": "985281530070265862",
    "awnihannun": "245262377",
    "GavinSBaker": "340387261",
    "FootnotesFirst": "90546527",
    "energybants": "3337913081",
    "tri_dao": "568879807",
    "firstadopter": "16598957",
}

# Cost tracking
cost_log = {
    "start_time": datetime.now().isoformat(),
    "accounts": {},
    "total_calls": 0,
    "total_tweets": 0,
    "total_filtered": 0,
}

def fetch_tweets(user_id, cursor=None):
    """Fetch tweets with cursor pagination"""
    url = f"{BASE_URL}?userId={user_id}"
    if cursor:
        url += f"&cursor={urllib.parse.quote(cursor)}"
    
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def filter_high_signal(tweets):
    """Filter out replies, retweets, keep only original high-signal content"""
    filtered = []
    for t in tweets:
        text = t.get("text", "")
        
        # Skip replies (starts with @)
        if text.startswith("@"):
            continue
        
        # Skip pure retweets (RT @)
        if text.startswith("RT @"):
            continue
        
        # Skip very short (< 50 chars)
        if len(text) < 50:
            continue
        
        # Skip if no substantive content
        if "http" in text and len(text) < 100:
            continue
        
        filtered.append(t)
    
    return filtered

def scrape_account(handle, user_id):
    """Full historical scrape for one account"""
    print(f"\n{'='*60}")
    print(f"Scraping @{handle} (ID: {user_id})")
    print(f"{'='*60}")
    
    all_tweets = []
    cursor = None
    page = 0
    max_pages = 50  # Safety limit
    
    account_log = {
        "user_id": user_id,
        "pages_fetched": 0,
        "total_raw": 0,
        "total_filtered": 0,
        "api_calls": 0,
        "start_time": datetime.now().isoformat(),
    }
    
    while page < max_pages:
        data = fetch_tweets(user_id, cursor)
        if not data:
            break
        
        tweets = data.get("tweets", [])
        if not tweets:
            print(f"  Page {page}: No more tweets")
            break
        
        all_tweets.extend(tweets)
        account_log["api_calls"] += 1
        account_log["total_raw"] += len(tweets)
        
        print(f"  Page {page}: {len(tweets)} tweets (total: {len(all_tweets)})")
        
        # Check if we've gone back far enough (2 years)
        # Just collect all available
        
        cursor = data.get("next_cursor")
        if not cursor:
            print(f"  No more pages")
            break
        
        page += 1
        time.sleep(0.5)  # Rate limit
    
    # Filter for high signal
    filtered = filter_high_signal(all_tweets)
    account_log["total_filtered"] = len(filtered)
    account_log["end_time"] = datetime.now().isoformat()
    
    # Save to file
    output = {
        "handle": handle,
        "user_id": user_id,
        "scraped_at": datetime.now().isoformat(),
        "total_raw": account_log["total_raw"],
        "total_filtered": account_log["total_filtered"],
        "tweets": filtered,
    }
    
    filepath = f"data/raw/{handle}_historical.json"
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  RESULT: {account_log['total_raw']} raw → {account_log['total_filtered']} filtered")
    print(f"  Saved to: {filepath}")
    
    return account_log

def main():
    print("=" * 60)
    print("HISTORICAL SCRAPE - PRIORITY 1 ACCOUNTS")
    print(f"Start: {datetime.now().isoformat()}")
    print(f"Cost: ~$0.001 per API call")
    print("=" * 60)
    
    for handle, user_id in ACCOUNTS.items():
        account_log = scrape_account(handle, user_id)
        cost_log["accounts"][handle] = account_log
        cost_log["total_calls"] += account_log["api_calls"]
        cost_log["total_tweets"] += account_log["total_filtered"]
        
        time.sleep(1)  # Between accounts
    
    cost_log["end_time"] = datetime.now().isoformat()
    cost_log["estimated_cost"] = cost_log["total_calls"] * 0.001
    
    # Save cost log
    with open("data/raw/scrape_log.json", "w") as f:
        json.dump(cost_log, f, indent=2)
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"Total API calls: {cost_log['total_calls']}")
    print(f"Total high-signal tweets: {cost_log['total_tweets']}")
    print(f"Estimated cost: ${cost_log['estimated_cost']:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
