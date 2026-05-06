import json
from openai import OpenAI


def extract_memory(messages, client, chunk_size=20):
    """
    카톡 메시지 리스트에서 '기억할 만한 정보'만 추출한다.
    """

    chunks = [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]
    memories = []

    for idx, chunk in enumerate(chunks):
        print(f"🧠 기억 추출 중... ({idx + 1}/{len(chunks)})")

        text = "\n".join(chunk)

        prompt = f"""
아래는 한 사람이 실제로 한 카카오톡 대화 내용이다.
이 사람의 '기억할 만한 사실'만 추출하라.

[추출 대상]
- 좋아하는 것
- 싫어하는 것
- 습관 / 반복 행동
- 자주 드러나는 성향
- 약속 / 계획 / 함께 하기로 한 것 (언제, 어디서, 무엇을 포함)

[주의]
- 말투, 감정 표현은 제외
- 추측하지 말고, 문장에 드러난 사실만 추출
- 애매하면 제외
- 약속/계획은 최대한 구체적으로 추출 (예: "다음 주 일요일에 놀이공원 가기로 함")

대화 내용:
{text}

출력(JSON):
{{
  "likes": [],
  "dislikes": [],
  "habits": [],
  "facts": [],
  "plans": []
}}
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 대화에서 사람의 성향과 사실, 약속/계획을 추출하는 AI다."},
                {"role": "user", "content": prompt}
            ]
        )

        content = res.choices[0].message.content

        print("\n===== GPT RAW RESPONSE =====")
        print(content)
        print("===== END =====\n")

        try:
            clean = content.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())

            # plans 항목이 dict면 문자열로 변환
            for key in ["likes", "dislikes", "habits", "facts", "plans"]:
                normalized = []
                for item in parsed.get(key, []):
                    if isinstance(item, dict):
                        normalized.append(json.dumps(item, ensure_ascii=False))
                    elif item:
                        normalized.append(str(item))
                parsed[key] = normalized

            memories.append(parsed)
        except json.JSONDecodeError:
            print(f"⚠️ JSON 파싱 실패, 해당 chunk 스킵\n내용: {content}")

    return memories