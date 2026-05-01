# ==========================================================
# 파일: src/core/gpt_core.py
# 역할: GPT API 통신과 클라이언트 초기화를 담당합니다.
# ==========================================================

import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 로드를 위한 경로 설정 (프로젝트 루트 경로 기준)
# 현재 위치: src/core/ -> 루트: ../../
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")
load_dotenv(ENV_PATH)

# 전역 클라이언트 변수
# 환경 변수 "OPENAI_API_KEY"에 저장된 값을 가져옵니다.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 초기 페르소나 프롬프트 (app_gui.py에서 생성된 실제 프롬프트로 덮어쓰여야 함)
current_persona_prompt = "초기 AI 모델 준비 중. 페르소나 로딩을 기다리세요." 


def chat_with_persona(system_prompt, user_message, chat_history):
    slow_speed_instruction = """
    # 중요 지시사항:
    1. 답변은 반드시 2~3문장 이내로 짧게 해주세요.
    2. 문장 사이사이에 쉼표(,)와 마침표(.)를 아주 많이 사용해서 천천히 말하는 느낌을 주세요.
    3. 한 문장이 끝나면 반드시 줄바꿈을 해주세요.
    """
    
    # 기존 프롬프트와 합치기
    enhanced_prompt = system_prompt + slow_speed_instruction

    messages = [
        # ✅ 이 부분에서 system_prompt(페르소나)가 반드시 첫 번째여야 합니다.
        {"role": "system", "content": enhanced_prompt},
    ]
    # 이전 대화 기록 추가...
    messages.append({"role": "user", "content": user_message})
    
    # OpenAI API 호출...
    
    # 문맥 유지를 위해 대화 기록 추가
    for item in chat_history: 
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