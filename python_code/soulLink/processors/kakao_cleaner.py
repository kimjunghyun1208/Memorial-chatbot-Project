import os
import re

# kakao_cleaner.py의 절대경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def extract_user_messages(filename, target_name):
    """
    카톡 txt 파일에서 특정 사용자의 메시지만 추출.
    filename: data 폴더 안의 파일 이름
    """

    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

    messages = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    pattern = re.compile(rf"^{target_name} : (.*)")

    for line in lines:
        match = pattern.match(line)
        if match:
            text = match.group(1).strip()

            if text in ["사진", "이모티콘", "동영상", "삭제된 메시지입니다."]:
                continue

            messages.append(text)

    return messages


# 테스트
if __name__ == "__main__":
    msgs = extract_user_messages("sample.txt", "홍길동")
    print(msgs[:20])
