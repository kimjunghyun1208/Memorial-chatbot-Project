# ==========================================================
# 파일: src/core/gpt_core.py
# 역할: GPT API 통신과 클라이언트 초기화를 담당합니다.
# ==========================================================

import os
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_chat_history(chat_history: list) -> str:
    """
    대화 기록이 길어지면 GPT로 요약하여 압축합니다.
    약속, 장소, 날짜, 중요한 정보 위주로 3~5줄 요약.
    """
    text = "\n".join([
        f"{'나' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in chat_history
    ])

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "아래 대화를 핵심 내용만 3~5줄로 요약해줘. "
                        "약속, 장소, 날짜, 함께 하기로 한 것, 중요한 감정이나 사실 위주로 요약해줘. "
                        "불필요한 인사나 감탄사는 제외해줘."
                    )
                },
                {"role": "user", "content": text}
            ]
        )
        summary = res.choices[0].message.content
        print(f"✅ [요약] 대화 {len(chat_history)}개 → 요약 완료")
        return summary
    except Exception as e:
        print(f"⚠️ 대화 요약 실패: {e}")
        return ""


def chat_with_persona(system_prompt: str, user_message: str, chat_history: list) -> str:
    """
    GPT에 페르소나 + 대화 기록 + 사용자 메시지를 전달하고 답변을 반환합니다.

    Args:
        system_prompt: 페르소나 + 기억 프롬프트
        user_message: 현재 사용자 메시지
        chat_history: 이전 대화 기록 [{"role": "user"/"assistant", "content": "..."}]

    Returns:
        GPT 답변 문자열
    """
    slow_speed_instruction = """

# 중요 지시사항:
1. 답변은 반드시 2~3문장 이내로 짧게 해주세요.
2. 문장 사이사이에 쉼표(,)와 마침표(.)를 많이 사용해서 천천히 말하는 느낌을 주세요.
3. 한 문장이 끝나면 반드시 줄바꿈을 해주세요.
"""

    messages = [
        {"role": "system", "content": system_prompt + slow_speed_instruction},
    ]

    # 이전 대화 기록 추가 (최근 20개만 유지 — 토큰 절약)
    for item in chat_history[-20:]:
        role = "user" if item["role"] == "user" else "assistant"
        messages.append({"role": role, "content": item["content"]})

    # 현재 사용자 메시지 추가
    messages.append({"role": "user", "content": user_message})

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"[GPT API 오류] 답변 생성 중 문제 발생: {str(e)}"