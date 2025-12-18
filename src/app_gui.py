import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import numpy as np

from core.voice_util import play_cloned_voice

from core import gpt_core 
from core.persona_process.kakao_cleaner import extract_user_messages
from core.persona_process.style_extractor import analyze_style, merge_analyses
from core.persona_process.persona_builder import build_persona

# GPT 작업 스레드
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

# 메인 GUI 클래스
class AIChatBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memorial-chatbot-Project")
        self.setGeometry(200, 200, 700, 750)
        self.chat_history = []
        self.persona_prompt = None
        
        # ✅ 해결 1: UI를 먼저 생성해야 label 관련 오류가 안 납니다.
        self.init_ui()
        # ✅ 해결 2: UI 생성 후 데이터를 로드합니다.
        self._load_persona_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        title_label = QLabel("✨ AI 추모 챗봇")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; color: #3498db; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)

        self.file_load_button = QPushButton("📁 음성 파일 불러오기")
        self.file_load_button.clicked.connect(self.load_audio_file)
        input_hbox.addWidget(self.file_load_button)

        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setStyleSheet("background-color: #2c2c2c; color: white; border-radius: 10px; padding: 10px;")
        layout.addWidget(self.chat_output)
        
        self.status_label = QLabel("시스템 초기화 중...")
        self.status_label.setStyleSheet("color: #2ecc71;")
        layout.addWidget(self.status_label)

        input_hbox = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("메시지를 입력하세요...")
        self.chat_input.returnPressed.connect(lambda: self.send_message(self.chat_input.text().strip()))
        
        self.send_button = QPushButton("전송")
        self.send_button.clicked.connect(lambda: self.send_message(self.chat_input.text().strip()))

        input_hbox.addWidget(self.chat_input)
        input_hbox.addWidget(self.send_button)
        layout.addLayout(input_hbox)

        # 초기 환영 메시지 추가
        self.chat_output.append(self._format_bot_message("안녕하세요! 시스템을 준비 중입니다."))

    # ✅ 해결 3: 오류가 났던 메시지 포맷 함수들을 정의합니다.
    def _format_user_message(self, text):
        return f"<div style='margin: 5px; text-align: right;'><b style='color: #f1c40f;'>나:</b> {text}</div>"

    def _format_bot_message(self, text):
        return f"<div style='margin: 5px; text-align: left;'><b style='color: #3498db;'>AI:</b> {text}</div>"

    def _load_persona_data(self):
        try:
            self.status_label.setText("⚙️ 카톡 데이터 분석 중...")
            QApplication.processEvents() # UI 업데이트 강제 적용

            # 데이터 로드 (이름 "홍길동" 확인 필수)
            msgs = extract_user_messages("sample.txt", "홍길동")
            analyses = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            
            self.status_label.setText("🟢 준비 완료! 대화를 시작하세요.")
        except Exception as e:
            self.status_label.setText(f"🔴 로드 실패: {str(e)}")

    def send_message(self, text):
        if not text or not self.persona_prompt: return
        self.chat_output.append(self._format_user_message(text))
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": text})
        
        self.worker = GPTWorker(text, self.chat_history, self.persona_prompt)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.start()

    def handle_response(self, response):
        self.chat_history.append({"role": "assistant", "content": response})
        self.chat_output.append(self._format_bot_message(response))
        self.chat_output.ensureCursorVisible()

    def load_audio_file(self):
        """컴퓨터에서 음성 파일을 선택하여 처리합니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "음성 파일 선택", "", "Audio Files (*.wav *.mp3 *.m4a)"
        )
    
        if file_path:
            self.status_label.setText(f"📂 파일 로드됨: {os.path.basename(file_path)}")
        
            # ⚠️ 실제 STT(음성->텍스트) 연동 전까지는 테스트 문구로 작동합니다.
            # 고퀄리티를 원하시면 여기서 OpenAI Whisper API를 호출해야 합니다.
            user_text = "불러온 음성 파일의 내용을 분석 중입니다..." 
            self.send_message(user_text) # GPT에게 전달

    def handle_response(self, response):
        """GPT 답변을 텍스트로 보여주고 ElevenLabs로 들려줍니다."""
        self.chat_history.append({"role": "assistant", "content": response})
        self.chat_output.append(self._format_bot_message(response))
    
        # ElevenLabs 음성 출력 실행
        play_cloned_voice(response)