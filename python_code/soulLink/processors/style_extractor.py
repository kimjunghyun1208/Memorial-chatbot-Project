import os
from openai import OpenAI
import json

from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_style(messages, chunk_size=30):
    """
    카톡 메시지 리스트를 받아 말투/성격 분석 JSON을 반환.
    """

    chunks = [messages[i:i+chunk_size] for i in range(0, len(messages), chunk_size)]
    analyses = []

    for idx, c in enumerate(chunks):
        print(f"▶ {idx+1}번째 메시지 묶음 분석 중…")

        text_block = "\n".join(c)

        prompt = f"""
        아래는 한 사람이 실제 카카오톡에서 작성한 메시지들이다.
        이 사람의 말투, 성격, 자주 쓰는 표현, 문장 구조를 분석하라.

        메시지 예시:
        {text_block}

        출력 형식(JSON만 출력):
        {{
            "tone": "말투 특징",
            "phrases": ["자주 쓰는 표현1", "자주 쓰는 표현2"],
            "behavior": "대화 스타일 및 성격",
            "summary": "전체 느낌 요약"
        }}
        """

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 언어 스타일 분석 전문가입니다. JSON만 출력하세요."},
                {"role": "user", "content": prompt}
            ]
        )

        # 최신 SDK 방식
        content = res.choices[0].message.content

        # 문자열을 JSON으로 파싱
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # 모델이 JSON을 조금 틀려서 보냈을 때 보정
            fixed = content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(fixed)

        analyses.append(parsed)

    return analyses


def merge_analyses(analyses):
    """
    여러 개의 분석 JSON을 취합해 하나의 페르소나를 생성.
    """
    final_prompt = {
        "tone": [],
        "phrases": [],
        "behavior": [],
        "summary": []
    }

    # 각각을 합치기
    for a in analyses:
        final_prompt["tone"].append(a.get("tone", ""))
        final_prompt["phrases"].extend(a.get("phrases", []))
        final_prompt["behavior"].append(a.get("behavior", ""))
        final_prompt["summary"].append(a.get("summary", ""))

    return final_prompt


if __name__ == "__main__":
    sample_msgs = [
        "오늘 뭐해?",
        "나 지금 카페야 ㅎㅎ",
        "뭐 먹을까 고민중",
        "오케이~ 조금만 기다려!",
    ]

    result = analyze_style(sample_msgs)
    final = merge_analyses(result)

    print("\n===== 최종 말투/성격 분석 =====\n")
    print(json.dumps(final, ensure_ascii=False, indent=4))
