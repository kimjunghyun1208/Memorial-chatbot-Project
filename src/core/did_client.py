import os
import requests
import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

DID_API_KEY = os.getenv("DID_API_KEY")
XI_API_KEY  = os.getenv("XI_API_KEY")
VOICE_ID    = os.getenv("VOICE_ID")

DID_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Basic {DID_API_KEY}"
}


def _generate_elevenlabs_audio(text: str) -> str | None:
    """
    ElevenLabs로 음성 생성 후 로컬에 저장하고 경로 반환.
    """
    current_voice_id = os.environ.get("VOICE_ID", VOICE_ID)
    if not XI_API_KEY or not current_voice_id:
        print("⚠️ ElevenLabs 설정 없음, D-ID 자체 TTS 사용")
        return None

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
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            print(f"⚠️ ElevenLabs 오류: {response.status_code}")
            return None

        # 로컬 저장
        audio_path = os.path.join(BASE_DIR, "temp_did_audio.mp3")
        with open(audio_path, "wb") as f:
            f.write(response.content)

        print(f"✅ ElevenLabs 음성 생성 완료: {audio_path}")
        return audio_path

    except Exception as e:
        print(f"⚠️ ElevenLabs 오류: {e}")
        return None


def _upload_audio_to_did(audio_path: str) -> str | None:
    """
    로컬 음성 파일을 D-ID 서버에 업로드하고 audio_url 반환.
    """
    try:
        with open(audio_path, "rb") as f:
            response = requests.post(
                "https://api.d-id.com/audios",
                headers={"authorization": f"Basic {DID_API_KEY}"},
                files={"audio": ("audio.mp3", f, "audio/mpeg")}
            )

        print(f"[DEBUG] D-ID 오디오 업로드: {response.status_code} - {response.text}")

        if response.status_code == 201:
            audio_url = response.json().get("url")
            print(f"✅ D-ID 오디오 업로드 완료: {audio_url}")
            return audio_url
        else:
            print(f"⚠️ D-ID 오디오 업로드 실패: {response.status_code}")
            return None

    except Exception as e:
        print(f"⚠️ D-ID 오디오 업로드 오류: {e}")
        return None


def upload_image_to_did(image_path: str) -> str | None:
    url = "https://api.d-id.com/images"
    headers = {"Authorization": f"Basic {DID_API_KEY}"}
    print(f"[DEBUG] 이미지 업로드 시도: {image_path}")
    print(f"[DEBUG] 파일 존재 여부: {os.path.exists(image_path)}")
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(url, files=files, headers=headers)
    print(f"[DEBUG] 업로드 응답: {response.status_code} - {response.text}")
    return response.json().get("url") if response.status_code == 201 else None


def generate_avatar_video(text: str, image_path_or_url: str) -> str | None:
    """
    텍스트 + 이미지 → D-ID 영상 생성.
    ElevenLabs 음성을 D-ID에 직접 업로드하여 싱크 문제 해결.
    """
    # 1. 이미지 준비
    if os.path.exists(image_path_or_url):
        source_url = upload_image_to_did(image_path_or_url)
    else:
        source_url = image_path_or_url

    if not source_url:
        print("❌ 이미지 업로드 실패")
        return None

    # 2. ElevenLabs 음성 생성 → D-ID 업로드
    audio_path = _generate_elevenlabs_audio(text)
    audio_url = None

    if audio_path:
        audio_url = _upload_audio_to_did(audio_path)

    # 3. 영상 생성 payload 구성
    if audio_url:
        # ElevenLabs 음성으로 D-ID 영상 생성 (싱크 완벽)
        script = {
            "type": "audio",
            "audio_url": audio_url
        }
        print("🎬 ElevenLabs 음성으로 D-ID 영상 생성 중...")
    else:
        # 폴백: D-ID 자체 TTS
        script = {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "ko-KR-SunHiNeural"}
        }
        print("🎬 D-ID 자체 TTS로 영상 생성 중...")

    payload = {
        "script": script,
        "source_url": source_url,
        "config": {
            "stitch": False,
            "fluent": True,
            "pad_audio": 2.5
        },
        "face_config": {
            "size": 512
        }
    }

    response = requests.post(
        "https://api.d-id.com/talks",
        json=payload,
        headers=DID_HEADERS
    )

    if response.status_code != 201:
        print(f"❌ D-ID 영상 생성 실패: {response.status_code} - {response.text}")
        return None

    talk_id = response.json().get("id")

    # 4. 완료 대기
    while True:
        time.sleep(3)
        res = requests.get(
            f"https://api.d-id.com/talks/{talk_id}",
            headers=DID_HEADERS
        )
        data = res.json()
        status = data.get("status")

        if status == "done":
            print(f"✅ D-ID 영상 완료")
            return data.get("result_url")
        elif status == "error":
            print(f"❌ D-ID 영상 실패: {data}")
            return None

        print(f"⏳ 진행 중... ({status})")