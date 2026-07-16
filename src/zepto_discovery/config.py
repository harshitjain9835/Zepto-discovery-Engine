from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", str(DATA_DIR / "raw")))
PROCESSED_DATA_DIR = Path(os.getenv("PROCESSED_DATA_DIR", str(DATA_DIR / "processed")))

for directory in (DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)

SOURCE_URLS = {
    "play_store": os.getenv("SOURCE_PLAY_STORE_URL", "https://play.google.com/store/apps/details?id=com.zeptoconsumerapp&hl=en_IN"),
    "app_store": os.getenv("SOURCE_APP_STORE_URL", "https://apps.apple.com/in/app/zepto-groceries-in-minutes/id1575323645?see-all=reviews&platform=iphone"),
    "reddit": os.getenv("SOURCE_REDDIT_URL", "https://www.reddit.com/search/?q=Reviews+of+Zepto+Service+in+india&cId=f4c2ed62-4010-40b0-9738-cc673e019b94&iId=52089c62-0722-4478-9394-f24d1ed62e95"),
}
