# core/persona_process/audio_extractor.py
from moviepy import VideoFileClip
import os

def extract_audio(video_path):
    """
    동영상 경로를 넣으면 같은 폴더에 .mp3 파일을 만들고 그 경로를 반환합니다.
    """
    try:
        # 1. 파일명 설정 (예: video.mp4 -> video.mp3)
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}.mp3"
        
        # 2. 오디오 추출
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_path)
        video.close() # 리소스 해제
        
        print(f"--- 음원 추출 성공: {output_path} ---")
        return output_path
    except Exception as e:
        print(f"--- 음원 추출 실패: {e} ---")
        return None