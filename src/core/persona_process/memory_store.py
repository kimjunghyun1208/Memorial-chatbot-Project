import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEMORY_DIR  = os.path.join(BASE_DIR, "data", "memory")
MEMORY_FILE = os.path.join(MEMORY_DIR, "persona_memory.json")


def ensure_memory_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)


def load_memory() -> dict:
    ensure_memory_dir()
    if not os.path.exists(MEMORY_FILE):
        return {
            "likes": [],
            "dislikes": [],
            "habits": [],
            "facts": [],
            "plans": []     # ← 약속/계획 추가
        }
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 기존 파일에 plans 없으면 추가
    if "plans" not in data:
        data["plans"] = []
    return data


def save_memory(memory: dict):
    ensure_memory_dir()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def merge_memories(old: dict, new_chunks: list) -> dict:
    def to_str_set(items):
        """딕셔너리/비문자열 항목을 안전하게 문자열로 변환 후 set으로"""
        result = set()
        for item in items:
            if isinstance(item, dict):
                result.add(json.dumps(item, ensure_ascii=False))
            elif item:
                result.add(str(item))
        return result

    merged = {
        "likes":    to_str_set(old.get("likes", [])),
        "dislikes": to_str_set(old.get("dislikes", [])),
        "habits":   to_str_set(old.get("habits", [])),
        "facts":    to_str_set(old.get("facts", [])),
        "plans":    to_str_set(old.get("plans", [])),
    }

    for chunk in new_chunks:
        for key in merged.keys():
            merged[key].update(to_str_set(chunk.get(key, [])))

    return {k: list(v) for k, v in merged.items()}