import sys
import os

# 1. src 폴더를 파이썬 경로에 추가하여 모듈 임포트가 가능하게 설정
# 프로젝트 루트 경로 확보
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from PyQt6.QtWidgets import QApplication
from app_gui import AIChatBotGUI # src/app_gui.py에서 클래스 로드

def main():
    """
    Memorial-chatbot-Project 실행 진입점
    """
    # 2. 필수 폴더 존재 여부 확인 및 생성
    required_dirs = ["config", "data", "src/core/persona_process"]
    for d in required_dirs:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

    # 3. .env 파일 확인 안내
    env_path = os.path.join(BASE_DIR, "config", ".env")
    if not os.path.exists(env_path):
        print(f"⚠️ 경고: {env_path} 파일이 없습니다. OpenAI API 키를 설정해주세요.")

    # 4. GUI 애플리케이션 시작
    app = QApplication(sys.argv)
    
    # 테마 설정 (선택 사항: 다크 모드 폰트 등 가독성 향상)
    app.setStyle("Fusion")
    
    window = AIChatBotGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()