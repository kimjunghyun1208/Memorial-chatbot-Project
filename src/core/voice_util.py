import os
import requests
import pygame
import time
from dotenv import load_dotenv
from pydub import AudioSegment

# ==========================================
# ElevenLabs 설정
# ==========================================
load_dotenv("config/.env")
XI_API_KEY = os.getenv("XI_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")

def play_cloned_voice(text):
    """텍스트를 ElevenLabs 목소리로 변환하여 실시간 재생합니다."""
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
            "stability": 0.9,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True,
            "speaking_rate": 0.7   # ← 이 줄 추가 (1.0이 기본, 낮을수록 느림, 0.7~0.9 권장)
        }
    }

    try:
        # 재생 중인 오디오 정지
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            time.sleep(0.3)

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            # Wav2Lip 호환을 위해 고정된 임시 파일명 사용
            temp_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp_voice.mp3")
            temp_filename = os.path.normpath(temp_filename)
            for _ in range(5):
                try:
                    with open(temp_filename, "wb") as f:
                        f.write(response.content)
                    break
                except PermissionError:
                    time.sleep(0.3)
            
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            print(f"✅ 재생 시작: {temp_filename}")
        else:
            print(f"⚠️ ElevenLabs API 오류: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ 음성 처리 중 오류 발생: {e}")
def slow_down_audio(file_path, speed=0.7):
    # 오디오 로드
    audio = AudioSegment.from_file(file_path)
    
    # 샘플 레이트를 조절하여 속도 변경
    new_sample_rate = int(audio.frame_rate * speed)
    slow_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
    
    # 다시 mp3로 저장 (표준 샘플 레이트로 변환)
    slow_audio = slow_audio.set_frame_rate(audio.frame_rate)
    slow_audio.export(file_path, format="mp3")
