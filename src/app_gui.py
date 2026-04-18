import sys
import os
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl, QSize
from PyQt6.QtGui import QPixmap
import speech_recognition as sr
from openai import OpenAI

# 기존 코어 모듈 임포트
from core.voice_util import play_cloned_voice
from core import gpt_core 
from core.persona_process.kakao_cleaner import extract_user_messages
from core.persona_process.style_extractor import analyze_style, merge_analyses
from core.persona_process.persona_builder import build_persona
from core.persona_process.memory_extractor import extract_memory
from core.persona_process.memory_prompt_builder import build_memory_prompt
from core.persona_process.memory_store import load_memory, merge_memories, save_memory
from core.did_client import generate_avatar_video 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GPTWorker(QThread):
    response_ready = pyqtSignal(str)
    def __init__(self, user_message: str, chat_history: list, system_prompt: str):
        super().__init__()
        self.user_message = user_message
        self.chat_history = chat_history 
        self.system_prompt = system_prompt
    def run(self):
        bot_response = gpt_core.chat_with_persona(
            system_prompt=self.system_prompt,
            user_message=self.user_message,
            chat_history=self.chat_history
        )
        self.response_ready.emit(bot_response)

class AIChatBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Digital Clone Project")
        self.setGeometry(100, 100, 1200, 800)
        self.chat_history = []
        self.auto_voice_enabled = True
        
        # ⭐ [중요] 내 컴퓨터에 있는 사진 파일 경로 설정
        # 프로젝트 폴더에 photo.jpg라는 이름으로 사진을 넣어두세요.
        self.avatar_photo_url = os.path.join(os.getcwd(), "photo.jpg") 

        self.init_ui()
        self._load_persona_data()

    def init_ui(self):
        main_hbox = QHBoxLayout(self)

        # --- [왼쪽: 디지털 클론 상시 노출 영역] ---
        video_container = QVBoxLayout()
        self.status_label = QLabel("시스템 준비 중...")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        
        # 영상 위젯 고정 (검은 배경과 테두리 설정)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(QSize(550, 550))
        
        # 만약 사진 파일이 존재하면 배경으로 깔아둡니다 (영상이 없을 때도 사진이 보이게 함)
        if os.path.exists(self.avatar_photo_url):
            self.video_widget.setStyleSheet(f"""
                background-image: url({self.avatar_photo_url.replace(os.sep, '/')});
                background-repeat: no-repeat;
                background-position: center;
                background-color: black;
                border: 2px solid #34495e;
                border-radius: 10px;
            """)
        else:
            self.video_widget.setStyleSheet("background-color: black; border: 2px solid #34495e; border-radius: 10px;")
        
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        video_container.addWidget(self.status_label)
        video_container.addWidget(self.video_widget, stretch=1)
        main_hbox.addLayout(video_container, stretch=1)

        # --- [오른쪽: 채팅 영역] ---
        chat_container = QVBoxLayout()
        title_label = QLabel("✨ AI MEMORIAL CHATBOT")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; color: #3498db; font-weight: bold; padding: 10px;")
        chat_container.addWidget(title_label)

        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setStyleSheet("background-color: #1e1e1e; color: #ecf0f1; border-radius: 10px; padding: 10px; font-size: 14px;")
        chat_container.addWidget(self.chat_output)

        input_hbox = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("메시지를 입력하세요...")
        self.chat_input.setFixedHeight(40)
        self.chat_input.returnPressed.connect(lambda: self.send_message(self.chat_input.text().strip()))
        
        self.send_button = QPushButton("전송")
        self.send_button.setFixedSize(70, 40)
        self.send_button.clicked.connect(lambda: self.send_message(self.chat_input.text().strip()))
        
        self.voice_record_button = QPushButton("🎤")
        self.voice_record_button.setFixedSize(50, 40)
        self.voice_record_button.clicked.connect(self.listen_and_send)

        input_hbox.addWidget(self.chat_input)
        input_hbox.addWidget(self.send_button)
        input_hbox.addWidget(self.voice_record_button)
        chat_container.addLayout(input_hbox)

        main_hbox.addLayout(chat_container, stretch=1)

    def _load_persona_data(self):
        try:
            self.status_label.setText("⚙️ 데이터 분석 중...")
            QApplication.processEvents()
            
            # 카카오톡 데이터 기반 페르소나 생성
            msgs = extract_user_messages("sample.txt", "홍길동")
            analyses = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            
            memory_chunks = extract_memory(msgs, client)
            existing_memory = load_memory()
            updated_memory = merge_memories(existing_memory, memory_chunks)
            save_memory(updated_memory)
            memory_prompt = build_memory_prompt(updated_memory)
            
            self.full_system_prompt = f"{self.persona_prompt}\n\n[기억]\n{memory_prompt}"
            self.status_label.setText("🟢 연결 완료: 대화가 가능합니다.")
            
        except Exception as e:
            self.status_label.setText(f"🔴 오류 발생: {str(e)}")

    def send_message(self, text):
        if not text or not hasattr(self, 'full_system_prompt'): return
        self.chat_output.append(f"<div style='text-align: right; color: #f1c40f;'><b>나:</b> {text}</div>")
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": text})
        
        self.status_label.setText("🤔 답변을 생각 중입니다...")
        self.worker = GPTWorker(text, self.chat_history, self.full_system_prompt)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.start()

    def handle_response(self, response):
        """GPT 답변 수신 후 영상 준비 단계로 바로 진입"""
        # 여기서 바로 텍스트를 띄우거나 소리를 내지 않고, 영상 제작 스레드에 모든 걸 맡깁니다.
        self.status_label.setText("🎬 고인이 답변 영상과 목소리를 준비 중입니다...")
        
        # D-ID 영상 생성 스레드 실행 (텍스트를 함께 넘김)
        threading.Thread(target=self.run_did_clone, args=(response,), daemon=True).start()

    def run_did_clone(self, text):
        """영상이 완성되는 시점에 맞춰 사운드와 텍스트를 동시에 출력"""
        # 1. D-ID 서버에서 영상 URL을 가져올 때까지 기다림 (약 10~15초 소요)
        video_url = generate_avatar_video(text, self.avatar_photo_url)
        
        if video_url:
            # 2. 영상이 준비되면 그제서야 채팅창에 텍스트 출력
            self.chat_history.append({"role": "assistant", "content": text})
            self.chat_output.append(f"<div style='text-align: left; color: #3498db;'><b>AI:</b> {text}</div>")
            self.chat_output.ensureCursorVisible()

            # 3. [중요] ElevenLabs 음성 재생을 영상 재생 직전에 실행
            if self.auto_voice_enabled:
                # 영상 시작과 거의 동시에 소리가 나오도록 여기서 호출합니다.
                threading.Thread(target=play_cloned_voice, args=(text,), daemon=True).start()

            # 4. 영상 재생 시작
            self.media_player.setSource(QUrl(video_url))
            self.media_player.play()
            self.status_label.setText("▶️ 답변 중...")
        else:
            # 실패 시 안내
            self.chat_output.append(f"<div style='text-align: left; color: #e74c3c;'><b>AI (오류):</b> {text}</div>")
            self.status_label.setText("❌ 영상 생성 실패")

    def listen_and_send(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.status_label.setText("🎤 듣고 있습니다...")
            QApplication.processEvents()
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=5)
                user_text = recognizer.recognize_google(audio, language='ko-KR')
                self.send_message(user_text)
            except Exception as e:
                self.status_label.setText("❌ 음성 인식 실패")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AIChatBotGUI()
    gui.show()
    sys.exit(app.exec())