# ==========================================================
# 파일: src/core/video_analyzer.py
# 역할: 동영상에서 음성 추출 + Whisper 텍스트 변환
#       + GPT-4o Vision 행동 분석 + 기억 저장
#       (pyannote 화자 분리 없이 동작)
# ==========================================================

import os
import json
import base64
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


# ──────────────────────────────────────────────
# 1. 동영상 → 전체 음성 추출
# ──────────────────────────────────────────────
def extract_full_audio(video_path: str) -> str:
    from moviepy.editor import VideoFileClip
    output_path = os.path.join(BASE_DIR, "temp_full_audio.mp3")
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_path, verbose=False, logger=None)
    clip.close()
    print(f"✅ 전체 오디오 추출 완료: {output_path}")
    return output_path


# ──────────────────────────────────────────────
# 2. Whisper로 음성 → 텍스트
# ──────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> list:
    import whisper
    print("🎙️ Whisper 음성 인식 중...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="ko")
    segments = [
        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
        for s in result["segments"]
    ]
    print(f"✅ 음성 인식 완료: {len(segments)}개 구간")
    return segments


# ──────────────────────────────────────────────
# 3. GPT-4o Vision 행동 분석
# ──────────────────────────────────────────────
def analyze_behavior_from_video(video_path: str, target_name: str, client, interval_sec: int = 3) -> list:
    import cv2

    print(f"\n👁️ GPT-4o Vision 행동 분석 시작 ({interval_sec}초 간격)")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0
    print(f"📹 영상 길이: {duration_sec:.1f}초, FPS: {fps:.1f}")

    frames_b64  = []
    frame_times = []
    interval_frames = max(1, int(fps * interval_sec))
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval_frames == 0:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            b64 = base64.b64encode(buffer).decode("utf-8")
            frames_b64.append(b64)
            frame_times.append(round(frame_idx / fps, 1))
        frame_idx += 1
    cap.release()

    print(f"✅ {len(frames_b64)}개 프레임 추출")

    if not frames_b64:
        return []

    behaviors = []
    batch_size = 5

    for i in range(0, len(frames_b64), batch_size):
        batch = frames_b64[i:i+batch_size]
        print(f"🔍 프레임 {i+1}~{i+len(batch)} 분석 중...")

        content = [
            {
                "type": "text",
                "text": (
                    f"아래 이미지들은 동영상에서 {interval_sec}초 간격으로 추출한 프레임입니다.\n"
                    f"영상 속 '{target_name}'의 행동, 표정, 자세, 습관을 분석해주세요.\n\n"
                    f"[분석 기준]\n"
                    f"- 어떤 행동을 하고 있는지 (예: 웃고 있음, 손을 흔들고 있음)\n"
                    f"- 표정이나 감정 (예: 밝은 표정, 진지한 표정)\n"
                    f"- 반복되는 제스처나 습관\n"
                    f"- 주변 환경이나 상황\n\n"
                    f"JSON 형식으로만 답해주세요:\n"
                    f"{{\"behaviors\": [\"행동1\", \"행동2\", ...]}}"
                )
            }
        ]
        for b64 in batch:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "low"
                }
            })

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": content}],
                max_tokens=500
            )
            raw = response.choices[0].message.content.strip()
            clean = raw
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            data = json.loads(clean.strip())
            batch_behaviors = data.get("behaviors", [])
            behaviors.extend(batch_behaviors)
            print(f"  → {len(batch_behaviors)}개 행동 감지")
        except Exception as e:
            print(f"⚠️ 프레임 분석 오류: {e}")
            continue

    behaviors = list(dict.fromkeys(behaviors))
    print(f"\n✅ 행동 분석 완료: {len(behaviors)}개 패턴")
    for b in behaviors:
        print(f"  - {b}")
    return behaviors


# ──────────────────────────────────────────────
# 4. 기억 저장
# ──────────────────────────────────────────────
def save_video_memory(segments: list, target_name: str, behaviors: list, client):
    from core.persona_process.memory_extractor import extract_memory
    from core.persona_process.memory_store import load_memory, merge_memories, save_memory

    messages = [s["text"] for s in segments if s["text"]]
    print(f"🧠 대화 기억 추출 중... ({len(messages)}개 발화)")

    memory_chunks = extract_memory(messages, client) if messages else []
    existing = load_memory()
    updated  = merge_memories(existing, memory_chunks)

    # 행동 패턴 → habits 저장
    if behaviors:
        updated.setdefault("habits", [])
        for b in behaviors:
            if isinstance(b, str) and b not in updated["habits"]:
                updated["habits"].append(b)
        print(f"✅ {len(behaviors)}개 행동 패턴 저장")

    # 대화 내용 → plans 저장
    if messages:
        updated.setdefault("plans", [])
        summary = f"[동영상 대화] " + " / ".join(messages[:15])
        if summary not in updated["plans"]:
            updated["plans"].append(summary)

    save_memory(updated)
    print(f"✅ 기억 저장 완료")


# ──────────────────────────────────────────────
# 메인 파이프라인
# ──────────────────────────────────────────────
def analyze_video(video_path: str, target_name: str, client) -> dict:
    print(f"\n🎬 동영상 분석 시작: {os.path.basename(video_path)}")
    print(f"👤 대상: {target_name}\n")

    # 1. 오디오 추출 (Whisper용)
    audio_path = extract_full_audio(video_path)

    # 2. 음성 인식
    segments = transcribe_audio(audio_path)

    # 3. GPT-4o Vision 행동 분석
    behaviors = analyze_behavior_from_video(video_path, target_name, client, interval_sec=3)

    # 4. 기억 저장 (음성 파일 ElevenLabs 전송 없음)
    save_video_memory(segments, target_name, behaviors, client)

    print(f"\n🎉 동영상 분석 완료!")
    print(f"  💬 대화: {len(segments)}개 구간")
    print(f"  👁️ 행동: {len(behaviors)}개 패턴")

    return {
        "conversation": segments,
        "behaviors":    behaviors
    }