import os
import requests
import time
from dotenv import load_dotenv

# 환경 변수 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

DID_API_KEY = os.getenv("DID_API_KEY")

def upload_image_to_did(image_path):
    """이미지를 D-ID 서버에 업로드"""
    url = "https://api.d-id.com/images"
    headers = {"Authorization": f"Basic {DID_API_KEY}"}
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(url, files=files, headers=headers)
    return response.json().get("url") if response.status_code == 201 else None

def generate_avatar_video(text, image_path_or_url):
    # 1. 이미지 준비
    if os.path.exists(image_path_or_url):
        source_url = upload_image_to_did(image_path_or_url)
    else:
        source_url = image_path_or_url

    if not source_url: return None

    # 2. [변경점] ElevenLabs 연동 대신 D-ID 표준 텍스트 방식을 우선 시도
    # (500 에러를 피하기 위해 가장 안전한 구조로 변경)
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {DID_API_KEY}"
    }

    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {
                "type": "microsoft",
                "voice_id": "ko-KR-SunHiNeural" # 일단 기본 목소리로 성공시키기
            }
        },
        "source_url": source_url,
        "config": {"stitch": True}
    }

    print("🎬 영상 생성 요청 중...")
    response = requests.post("https://api.d-id.com/talks", json=payload, headers=headers)
    
    if response.status_code != 201:
        print(f"❌ 오류: {response.status_code} - {response.text}")
        return None

    talk_id = response.json().get("id")
    
    # 3. 결과 대기 (Polling)
    while True:
        time.sleep(3)
        res = requests.get(f"https://api.d-id.com/talks/{talk_id}", headers=headers)
        data = res.json()
        if data.get("status") == "done":
            return data.get("result_url")
        elif data.get("status") == "error":
            print(f"❌ 생성 실패: {data}")
            return None
        print(f"⏳ 진행 중... ({data.get('status')})")