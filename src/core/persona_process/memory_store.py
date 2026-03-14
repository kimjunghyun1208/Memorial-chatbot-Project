import os
import json

# 프로젝트 루트 기준
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEMORY_DIR = os.path.join(BASE_DIR, "data", "memory")
MEMORY_FILE = os.path.join(MEMORY_DIR, "persona_memory.json")


def ensure_memory_dir():
    """memory 디렉토리 없으면 생성"""
    os.makedirs(MEMORY_DIR, exist_ok=True)


def load_memory():
    """
    저장된 기억 로드
    """
    ensure_memory_dir()

    if not os.path.exists(MEMORY_FILE):
        return {
            "likes": [],
            "dislikes": [],
            "habits": [],
            "facts": []
        }

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory: dict):
    """
    기억 저장
    """
    ensure_memory_dir()

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def merge_memories(old: dict, new_chunks: list):
    """
    기존 기억 + 새로 추출된 기억 병합
    중복 제거
    """
    merged = {
        "likes": set(old.get("likes", [])),
        "dislikes": set(old.get("dislikes", [])),
        "habits": set(old.get("habits", [])),
        "facts": set(old.get("facts", [])),
    }

    for chunk in new_chunks:
        for key in merged.keys():
            merged[key].update(chunk.get(key, []))

    # set → list 변환
    return {k: list(v) for k, v in merged.items()}
