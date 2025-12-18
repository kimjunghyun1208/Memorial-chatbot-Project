import os
import requests
import pygame

# ==========================================
# ElevenLabs 설정 (본인의 정보를 입력하세요)
# ==========================================
XI_API_KEY = "여러분의_에레븐랩스_API_키" 
VOICE_ID = "학습시킨_보이스_ID" 

def play_cloned_voice(text):
    """텍스트를 ElevenLabs 목소리로 변환하여 재생합니다."""
    # 한국어 모델 설정
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": XI_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # 한국어 지원 최신 모델
        "voice_settings": {
            "stability": 0.5,       # 목소리 안정성 (0~1)
            "similarity_boost": 0.75 # 원본과의 유사도 (0~1)
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            filename = "response_voice.mp3"
            # 기존 파일이 재생 중일 수 있으므로 안전하게 저장
            with open(filename, "wb") as f:
                f.write(response.content)
            
            # 오디오 재생 초기화 및 실행
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            print(f"✅ ElevenLabs 음성 출력 성공: {text[:20]}...")
        else:
            print(f"⚠️ ElevenLabs API 오류: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 음성 출력 처리 중 오류 발생: {e}")

# (기존에 있던 record_user_voice 함수 등이 필요 없다면 이대로 끝내셔도 됩니다.)