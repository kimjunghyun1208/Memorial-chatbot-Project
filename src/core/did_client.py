import os
import requests
import time
from dotenv import load_dotenv
from pydub import AudioSegment

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
            "provider": {"type": "microsoft", "voice_id": "ko-KR-SunHiNeural"}
        },
        "config": {
            "stitch": False,
            "fluent": True,
            "pad_audio": 0.0,
            "mute": True        # ← 이 줄 추가
        },
        "source_url": source_url,
        "config": {
            "stitch": False,
            "fluent": True,       # 부드러운 입 모양 및 효율 증대
            "pad_audio": 2.5  # ⭐ 음성 앞뒤에 자동으로 무음을 추가해주는 옵션 (단위: 초)
           
        },
        "face_config": {
            "size": 512           # 사진 처리 사이즈를 512로 제한하여 속도 향상
        }
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
def fix_sync_and_speed(file_path):
    # 1. 오디오 로드
    audio = AudioSegment.from_file(file_path)
    
    # 2. 속도를 0.92배속으로 미세하게 늦춤 (입 모양이 따라오기 쉽게)
    new_sample_rate = int(audio.frame_rate * 0.92)
    slow_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
    slow_audio = slow_audio.set_frame_rate(audio.frame_rate)
    
    # 3. 앞부분에 1.5초 무음 추가 (재생 시작 딜레이)
    silence = AudioSegment.silent(duration=1500)
    final_audio = silence + slow_audio
    
    # 4. 덮어쓰기
    final_audio.export(file_path, format="mp3")
    print("--- [완료] 음성 속도 조절 및 1.5초 딜레이 적용됨 ---")

def adjust_voice_tempo(file_path, speed=0.5):
    """
    음성 파일의 속도를 조절하여 영상과의 누적 싱크 오류를 방지합니다.
    0.95는 약 5% 정도 천천히 말하게 설정하는 값입니다.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        
        # 1. 샘플 레이트를 조절하여 속도를 변경 (0.95배속)
        # 소리가 늘어지면서 아주 미세하게 저음이 될 수 있으나 싱크에는 가장 확실합니다.
        new_sample_rate = int(audio.frame_rate * speed)
        slower_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        
        # 2. 표준 샘플 레이트로 다시 설정하여 파일 호환성 유지
        final_audio = slower_audio.set_frame_rate(audio.frame_rate)
        
        # 3. 기존 파일에 덮어쓰기
        final_audio.export(file_path, format="mp3")
        print(f"--- [성공] 음성 속도 {speed}배속 조절 완료 ---")
        
    except Exception as e:
        print(f"--- [오류] 속도 조절 중 문제 발생: {e} ---")

# 사용 시점: ElevenLabs에서 음성을 받은 직후, D-ID로 보내기 전!
# adjust_voice_tempo("voice.mp3", 0.95)