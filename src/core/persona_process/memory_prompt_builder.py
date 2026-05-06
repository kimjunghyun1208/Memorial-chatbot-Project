def build_memory_prompt(memory: dict) -> str:
    """
    저장된 기억 딕셔너리를 GPT 시스템 프롬프트용 텍스트로 변환합니다.
    행동 패턴이 대화에서 자연스럽게 반영되도록 상세히 작성합니다.
    """
    lines = []

    if memory.get("likes"):
        lines.append("[ 좋아하는 것 ]\n" + "\n".join(f"- {x}" for x in memory["likes"]))

    if memory.get("dislikes"):
        lines.append("[ 싫어하는 것 ]\n" + "\n".join(f"- {x}" for x in memory["dislikes"]))

    if memory.get("habits"):
        lines.append(
            "[ 습관 및 행동 패턴 ]\n"
            "아래는 이 사람이 실제로 보여준 행동 패턴과 습관입니다. "
            "대화할 때 이 행동 패턴을 자연스럽게 언급하거나 반영하세요.\n"
            + "\n".join(f"- {x}" for x in memory["habits"])
        )

    if memory.get("facts"):
        lines.append("[ 알려진 사실 ]\n" + "\n".join(f"- {x}" for x in memory["facts"]))

    if memory.get("plans"):
        lines.append(
            "[ 약속 / 계획 / 동영상 대화 내용 ]\n"
            "아래 내용을 기억하고 대화에서 자연스럽게 활용하세요.\n"
            + "\n".join(f"- {x}" for x in memory["plans"])
        )

    if not lines:
        return "아직 기억된 정보가 없습니다."

    header = (
        "=== 이 사람에 대해 기억하고 있는 정보 ===\n"
        "아래 정보를 바탕으로 이 사람처럼 자연스럽게 대화하세요. "
        "행동 패턴이나 습관은 대화 중 적절히 언급하거나 행동으로 표현하세요.\n\n"
    )

    return header + "\n\n".join(lines)