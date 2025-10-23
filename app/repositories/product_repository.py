import os
import json
from typing import List, Dict


# project root (two levels up from app/repositories)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def save_products(file_name: str, items: List[Dict]):
    path = os.path.join(BASE_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_products(file_name: str) -> List[Dict]:
    path = os.path.join(BASE_DIR, file_name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
