import os
import requests
import pygame
import time

# ==========================================
# ElevenLabs 설정
# ==========================================
XI_API_KEY = "sk_dda35c5de63c9756ca3f770dfdfc43c49dfcc407db036f62" # 따옴표 포함 확인
VOICE_ID = "y2skw7p6O7OxpMrhHOHw" # 학습시킨 Voice ID를 입력하세요

def play_cloned_voice(text):
    """텍스트를 ElevenLabs 목소리로 변환하여 재생합니다."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": XI_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        # ✅ 해결책 1: 재생 중인 오디오가 있다면 정지 및 점유 해제
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() 

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # ✅ 해결책 2: 파일명 충돌을 방지하기 위해 임시 파일 생성
            # 기존 response_voice.mp3 대신 시간값을 붙여서 생성합니다.
            temp_filename = f"temp_voice_{int(time.time())}.mp3"
            
            with open(temp_filename, "wb") as f:
                f.write(response.content)
            
            # 오디오 초기화 및 재생
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # ✅ 사용 완료된 임시 파일들은 나중에 정리하거나 유지합니다.
            print(f"✅ 재생 시작: {temp_filename}")
        else:
            print(f"⚠️ ElevenLabs API 오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 음성 처리 중 오류 발생: {e}")