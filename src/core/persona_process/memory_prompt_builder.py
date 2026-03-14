def build_memory_prompt(memory: dict) -> str:
    parts = []

    if memory.get("likes"):
        parts.append(f"좋아하는 것: {', '.join(memory['likes'])}")

    if memory.get("dislikes"):
        parts.append(f"싫어하는 것: {', '.join(memory['dislikes'])}")

    if memory.get("habits"):
        parts.append(f"습관: {', '.join(memory['habits'])}")

    if memory.get("facts"):
        parts.append(f"사실 정보: {', '.join(memory['facts'])}")

    if not parts:
        return "기억된 개인 정보 없음"

    return "\n".join(parts)
