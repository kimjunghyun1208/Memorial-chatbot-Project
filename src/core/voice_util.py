import os
import requests
import pygame
import time
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", ".env"
))

XI_API_KEY = os.getenv("XI_API_KEY")
VOICE_ID    = os.getenv("VOICE_ID")

# ──────────────────────────────────────────────
# 음성 클론 생성 (ElevenLabs API)
# ──────────────────────────────────────────────

def create_voice_clone(mp3_path: str, voice_name: str = "cloned_voice") -> str | None:
    """
    mp3 파일을 ElevenLabs에 업로드하여 음성 클론을 생성하고
    생성된 Voice ID를 반환합니다.

    반환값: Voice ID 문자열 (실패 시 None)
    """
    if not XI_API_KEY:
        print("❌ XI_API_KEY가 설정되지 않았습니다.")
        return None

    if not os.path.exists(mp3_path):
        print(f"❌ 파일 없음: {mp3_path}")
        return None

    print(f"[VoiceClone] '{voice_name}' 음성 클론 생성 중...")

    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": XI_API_KEY}

    with open(mp3_path, "rb") as f:
        files = [("files", (os.path.basename(mp3_path), f, "audio/mpeg"))]
        data  = {"name": voice_name}
        response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        voice_id = response.json().get("voice_id")
        print(f"✅ [VoiceClone] 완료! Voice ID: {voice_id}")
        return voice_id
    else:
        print(f"❌ [VoiceClone] 실패: {response.status_code} - {response.text}")
        return None


def save_voice_id_to_env(voice_id: str):
    """
    생성된 Voice ID를 config/.env 파일에 자동으로 저장합니다.
    기존 VOICE_ID 항목이 있으면 교체, 없으면 추가합니다.
    """
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config", ".env"
    )

    # 기존 .env 읽기
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # VOICE_ID 줄 교체 또는 추가
    found = False
    for i, line in enumerate(lines):
        if line.startswith("VOICE_ID="):
            lines[i] = f"VOICE_ID={voice_id}\n"
            found = True
            break

    if not found:
        lines.append(f"VOICE_ID={voice_id}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # 현재 프로세스 환경변수도 갱신
    os.environ["VOICE_ID"] = voice_id
    global VOICE_ID
    VOICE_ID = voice_id

    print(f"✅ [VoiceClone] Voice ID가 .env에 저장되었습니다: {voice_id}")


# ──────────────────────────────────────────────
# TTS 재생
# ──────────────────────────────────────────────

def play_cloned_voice(text: str):
    """
    텍스트를 ElevenLabs 클론 목소리로 변환하여 재생합니다.
    """
    current_voice_id = os.environ.get("VOICE_ID", VOICE_ID)

    if not current_voice_id:
        print("❌ VOICE_ID가 설정되지 않았습니다. 먼저 음성 클론을 생성해주세요.")
        return

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{current_voice_id}"
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
            "use_speaker_boost": True
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
            temp_filename = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "temp_voice.mp3"
            )
            temp_filename = os.path.normpath(temp_filename)

            # 파일 잠금 해제 대기 후 저장
            for _ in range(5):
                try:
                    with open(temp_filename, "wb") as f:
                        f.write(response.content)
                    break
                except PermissionError:
                    time.sleep(0.3)
            try:
                audio = AudioSegment.from_file(temp_filename)
                new_sample_rate = int(audio.frame_rate * 0.5)
                slow_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
                slow_audio = slow_audio.set_frame_rate(audio.frame_rate)
                slow_audio.export(temp_filename, format="mp3")
            except Exception as e:
                print(f"속도 조절 실패: {e}")

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            print(f"✅ 재생 시작: {temp_filename}")
        else:
            print(f"⚠️ ElevenLabs API 오류: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ 음성 처리 중 오류: {e}")