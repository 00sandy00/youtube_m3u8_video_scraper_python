import random
import time
import logging
import asyncio
from typing import List, Dict
import os
import json
import argparse
import sys
import httpx
from tqdm.asyncio import tqdm_asyncio

# Attempt to import required modules
try:
    import ssl
    import yt_dlp
except ModuleNotFoundError as e:
    raise ImportError("This script requires 'ssl', 'yt_dlp', and 'httpx'. Install them via pip.") from e

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CACHE_FILE = "proxy_cache.json"
CACHE_TTL = 24 * 60 * 60
RESULTS_JSON = "results.json"
MAX_PROXIES = 50
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

# Load and validate public proxies from GitHub sources
async def fetch_and_validate_proxies(limit: int = MAX_PROXIES) -> List[str]:
    logging.info("Fetching proxies from public sources...")
    raw_proxies = set()
    
    async with httpx.AsyncClient(timeout=10) as client:
        for url in PROXY_SOURCES:
            try:
                r = await client.get(url)
                raw_proxies.update(line.strip() for line in r.text.splitlines() if ":" in line)
            except Exception as e:
                logging.warning(f"Failed to fetch from {url}: {e}")

    logging.info(f"Fetched {len(raw_proxies)} unique proxies. Validating...")
    validated = []

    async def test(proxy: str):
        try:
            async with httpx.AsyncClient(proxies=f"http://{proxy}", timeout=5) as pclient:
                r = await pclient.get("http://httpbin.org/ip")
                if r.status_code == 200:
                    validated.append(f"http://{proxy}")
        except:
            pass

    tasks = [test(p) for p in list(raw_proxies)[:200]]
    await asyncio.gather(*tasks)
    logging.info(f"Validated {len(validated)} proxies.")
    return validated[:limit]

# Wrapper for proxy loading with caching
def load_proxies_sync() -> List[str]:
    logging.info("Checking proxy cache...")
    if os.path.exists(CACHE_FILE):
        modified_time = os.path.getmtime(CACHE_FILE)
        if time.time() - modified_time < CACHE_TTL:
            try:
                with open(CACHE_FILE, 'r') as f:
                    proxies = json.load(f)
                    if proxies:
                        logging.info(f"Loaded {len(proxies)} proxies from cache.")
                        return proxies
            except Exception as e:
                logging.warning(f"Failed to read cache: {e}")

    try:
        proxies = asyncio.run(fetch_and_validate_proxies())
        with open(CACHE_FILE, 'w') as f:
            json.dump(proxies, f)
        logging.info(f"Saved {len(proxies)} proxies to cache.")
        return proxies
    except Exception as e:
        logging.error(f"Failed to fetch proxies: {e}")
        return []

# Global proxy list
PROXIES = load_proxies_sync()

# Pick a random proxy
def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None

# Extract m3u8, title, and description from a video
def get_m3u8_link(video_url: str, retries: int = 1) -> Dict:
    logging.info(f"Getting m3u8 link for {video_url}")
    for attempt in range(1, retries + 2):
        proxy = get_random_proxy()
        ydl_opts = {
            'quiet': True,
            'format': 'best',
            'nocheckcertificate': True,
            'proxy': proxy,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                m3u8_url = info.get("url")
                if m3u8_url:
                    return {
                        "status": "SUCCESS",
                        "url": video_url,
                        "title": info.get("title"),
                        "description": info.get("description"),
                        "m3u8": m3u8_url,
                        "attempts": attempt,
                        "proxy": proxy
                    }
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {video_url} via {proxy}: {e}")
            time.sleep(random.uniform(1, 2))

    return {"status": "FAILED", "url": video_url, "m3u8": None, "attempts": retries + 1, "proxy": None}

# Async processing of each video
async def process_video(video_url: str) -> Dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_m3u8_link, video_url)

# Main scraper logic with progress bar
async def run_scraper(video_urls: List[str]):
    logging.info("Running scraper on video list")
    tasks = [process_video(url) for url in video_urls]
    results = await tqdm_asyncio.gather(*tasks)
    save_results(results)
    return results

# Save results
def save_results(results: List[Dict]):
    with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logging.info("Results saved to results.json")

# Run the scraper with event loop fallback
def run_main(video_urls):
    try:
        asyncio.run(run_scraper(video_urls))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_scraper(video_urls))
        loop.run_until_complete(task)

# Input parsing for CLI or prompt
def parse_video_inputs(inputs: List[str]) -> List[str]:
    urls = []
    for entry in inputs:
        parts = entry.replace(",", " ").split()
        for part in parts:
            part = part.strip()
            if part:
                urls.append(part if part.startswith("http") else f"https://www.youtube.com/watch?v={part}")
    return urls

# CLI entry
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube m3u8 extractor")
    parser.add_argument("urls", nargs='*', help="YouTube video URL(s) or ID(s)")
    args = parser.parse_args()

    if args.urls:
        video_urls = parse_video_inputs(args.urls)
    else:
        try:
            user_input = input("Enter one or more YouTube video URLs or IDs: ").strip()
            if not user_input:
                raise ValueError("No input received")
            video_urls = parse_video_inputs([user_input])
        except (OSError, ValueError):
            logging.warning("No input detected, using fallback video")
            video_urls = ["https://www.youtube.com/watch?v=Ym79qFpa7dQ"]

    run_main(video_urls)
