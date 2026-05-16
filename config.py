import os
import json

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

CONFIG_FILE = "config.json"

default = {
    "sudo": [],
    "delay": 3,
    "dp": 0.05,
    "mode": "batch",
    "max": 2,
    "ab_time": 180,
    "ab_text": "",
    "ab_status": False
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(default, f, indent=4)

with open(CONFIG_FILE) as f:
    config = json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get(k, d=None):
    return config.get(k, d)
