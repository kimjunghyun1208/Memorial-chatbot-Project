import os
from openai import OpenAI
from dotenv import load_dotenv

from processors.kakao_cleaner import extract_user_messages
from processors.style_extractor import analyze_style, merge_analyses
from processors.persona_builder import build_persona

# .env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chat_with_persona(system_prompt, user_message):
    """해당 사람 말투로 답변 생성"""
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return res.choices[0].message.content


if __name__ == "__main__":

    print("=== Step1. 카카오톡 메시지 로딩 ===")
    msgs = extract_user_messages("sample.txt", "홍길동")

    print("=== Step2. 말투 분석 ===")
    analyses = analyze_style(msgs)
    persona_json = merge_analyses(analyses)

    print("=== Step3. 페르소나 Prompt 생성 ===")
    system_prompt = build_persona(persona_json)

    print("\n=== 대화 시작 ===")
    print("그 사람의 말투로 챗봇이 답변합니다.\n-------------------------------------")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        reply = chat_with_persona(system_prompt, user_input)
        print("Bot:", reply)
