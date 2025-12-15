# ==========================================================
# 파일: src/app_gui.py
# 역할: PyQt6 GUI 구성, 페르소나 로딩, 스레드 관리 (C.txt + main.py 통합)
# ==========================================================

import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import numpy as np # RecorderWorker를 위해 필요

# 🟢 [1] 코어 및 페르소나 모듈 임포트
# .env 설정 및 API 통신 모듈
from src.core import gpt_core 

# 페르소나 생성 모듈
from src.core.persona_process.kakao_cleaner import extract_user_messages
from src.core.persona_process.style_extractor import analyze_style, merge_analyses
from src.core.persona_process.persona_builder import build_persona

# 음성 처리 모듈 (D.txt 기반)
# from src.core.voice_util import RecorderWorker 
# (현재 코드에는 포함하지 않지만, 실제 구현 시 임포트해야 합니다.)


# =======================================================================
# [2] GPT 작업자 스레드 (C.txt의 DLWorker 수정)
# =======================================================================
class GPTWorker(QThread):
    """
    백그라운드에서 GPT API와 통신하여 답변을 받아오는 스레드
    """
    response_ready = pyqtSignal(str) # 작업 완료 시 챗봇 응답을 GUI로 보내기 위한 시그널

    def __init__(self, user_message: str, chat_history: list, system_prompt: str):
        super().__init__()
        self.user_message = user_message
        self.chat_history = chat_history 
        self.system_prompt = system_prompt # 페르소나 프롬프트 (가장 중요)

    def run(self):
        """
        gpt_core.py의 chat_with_persona 함수를 호출하여 답변을 생성합니다.
        """
        if not self.system_prompt or self.system_prompt.startswith("[오류]"):
             self.response_ready.emit(self.system_prompt)
             return

        # 🟢 gpt_core.py의 함수를 호출하여 API 통신 수행
        bot_response = gpt_core.chat_with_persona(
            system_prompt=self.system_prompt,
            user_message=self.user_message,
            chat_history=self.chat_history
        )

        self.response_ready.emit(bot_response)


# =======================================================================
# [3] 메인 GUI 애플리케이션 클래스 (C.txt의 AIChatBotGUI 확장)
# =======================================================================
class AIChatBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memorial-chatbot-Project - AI 추모 챗봇")
        self.setGeometry(200, 200, 700, 750)
  
        self.current_worker = None
        self.chat_history = [] # 대화 문맥 저장을 위한 리스트
        self.persona_prompt = None # 🟢 최종 페르소나 프롬프트 저장 변수
        
        # 🟢 [Step 2] 페르소나 데이터 로딩을 초기화 단계에서 실행
        self._load_persona_data()
        
        self.init_ui()

    # -----------------------------------------------------
    # 🟢 페르소나 로딩 로직 (main.py의 if __name__ == "__main__" 블록)
    # -----------------------------------------------------
    def _load_persona_data(self):
        """ main.py의 Step 1, 2, 3 로직을 실행하여 프롬프트를 생성 """
        try:
            print("=== Step1. 카카오톡 메시지 로딩 ===")
            # *주의: '홍길동'은 data/sample.txt에 있는 실제 이름이어야 합니다.
            # 파일 경로 설정은 kakao_cleaner.py 내부에서 처리됩니다.
            msgs = extract_user_messages("sample.txt", "홍길동") 
            print(f"로드된 메시지 수: {len(msgs)}")
            self.status_label.setText("⚙️ 메시지 로딩 완료. GPT 분석 시작...")

            print("=== Step2. 말투 분석 (GPT API 호출) ===")
            analyses = analyze_style(msgs)
            persona_json = merge_analyses(analyses)

            print("=== Step3. 페르소나 Prompt 생성 ===")
            self.persona_prompt = build_persona(persona_json)
            
            # gpt_core 모듈의 프롬프트 업데이트 (참고용)
            gpt_core.current_persona_prompt = self.persona_prompt 
            
            print("✅ 페르소나 로딩 완료. 챗봇이 활성화됩니다.")
            self.status_label.setText("🟢 AI 모델 준비 완료. 질문을 입력하세요. (엔터키 전송)")

        except FileNotFoundError:
            self.persona_prompt = "[오류] data/sample.txt 파일을 찾을 수 없습니다. 경로를 확인하세요."
            print(self.persona_prompt)
            self.status_label.setText("🔴 오류: 페르소나 파일 로드 실패")
        except Exception as e:
            self.persona_prompt = f"[오류] 페르소나 생성 중 문제 발생: {str(e)}. (API 키, 네트워크 확인)"
            print(self.persona_prompt)
            self.status_label.setText("🔴 오류: GPT 페르소나 생성 실패")


    # -----------------------------------------------------
    # GUI 기본 구성 (C.txt의 init_ui)
    # -----------------------------------------------------
    def init_ui(self):
        # ... (C.txt의 QSS 스타일 설정은 동일하게 유지) ...
        self.setStyleSheet("""...""") # 스타일 시트 내용
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 타이틀
        title_label = QLabel("✨ AI 추모 챗봇 GUI")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        title_label.setStyleSheet(""" QLabel { font-size: 28px; font-weight: 600; color: #3498db; padding: 10px; } """)
        layout.addWidget(title_label)

        # 채팅 출력창
        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setStyleSheet(""" QTextEdit { background-color: #2c2c2c; border: 1px solid #3a3a3a; padding: 15px; border-radius: 15px; font-size: 15px; color: #ecf0f1; line-height: 1.5; } """)
        layout.addWidget(self.chat_output)
        
        # 💡 상태 표시창 (_load_persona_data에서 초기 상태가 설정됨)
        self.status_label = QLabel("로딩 중...")
        self.status_label.setStyleSheet("color: #2ecc71; padding-top: 5px; font-weight: bold;") 
        layout.addWidget(self.status_label)

        # 🎤 음성 녹음 버튼 (RecorderWorker 사용 시 활성화)
        self.record_button = QPushButton("🎤 음성 녹음 (5초)")
        # self.record_button.clicked.connect(self.start_recording) # D.txt 통합 후 연결
        self.record_button.setStyleSheet(""" ... """) # 스타일 시트 내용
        
        # 입력 컨테이너
        input_hbox = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("메시지를 입력하고 엔터 키를 누르세요...")
        self.chat_input.returnPressed.connect(lambda: self.send_message(self.chat_input.text().strip())) 
        self.chat_input.setStyleSheet(""" ... """) # 스타일 시트 내용
        
        input_hbox.addWidget(self.chat_input)
        input_hbox.addWidget(self.record_button)
        
        input_container = QFrame()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addLayout(input_hbox)
        layout.addWidget(input_container)
        
        # 초기 환영 메시지
        self.chat_output.append(self._format_bot_message("안녕하세요! AI 챗봇 시스템 초기화를 시작합니다."))

    # -----------------------------------------------------
    # 메시지 전송 및 응답 처리 (C.txt의 send_message, handle_response 확장)
    # -----------------------------------------------------
    def send_message(self, user_msg: str):
        """ 텍스트 메시지를 전송하고 GPTWorker를 시작합니다. """
        
        if not user_msg or (self.current_worker and self.current_worker.isRunning()):
            return

        # 1. 사용자 메시지 출력
        self.chat_output.append(self._format_user_message(user_msg))
        self.chat_input.clear()
        
        # 2. 대화 기록에 추가 (role='user'로 저장)
        self.chat_history.append({"role": "user", "content": user_msg})

        # 3. GUI 비활성화 및 상태 업데이트
        self._set_gui_disabled(True)
        self.status_label.setText("⏳ GPT 모델이 답변을 생성 중입니다...")
        
        # 4. 🟢 GPTWorker 스레드 시작 (수정된 부분)
        self.current_worker = GPTWorker(
            user_message=user_msg, 
            chat_history=self.chat_history,
            system_prompt=self.persona_prompt # 🟢 가장 중요: 생성된 페르소나 프롬프트 전달
        ) 
        self.current_worker.response_ready.connect(self.handle_response)
        self.current_worker.start() 
        self.chat_output.ensureCursorVisible()

    def handle_response(self, response: str):
        """ GPTWorker로부터 최종 응답을 받아 GUI에 표시하는 슬롯입니다. """
        
        # 1. GUI 복구
        self._set_gui_disabled(False)
        self.status_label.setText("✅ 답변 수신 완료. 새로운 메시지를 입력하세요.")

        # 2. 대화 기록에 추가 (role='bot'으로 저장)
        self.chat_history.append({"role": "bot", "content": response})

        # 3. 타이핑 효과로 출력
        self.display_typing_effect(response)
        
        self.current_worker = None
        self.chat_output.ensureCursorVisible()

    # -----------------------------------------------------
    # 헬퍼 함수 (C.txt의 나머지 로직)
    # -----------------------------------------------------
    def _set_gui_disabled(self, disabled: bool):
        """ 입력 관련 GUI 요소를 비활성화/활성화합니다. """
        self.chat_input.setEnabled(not disabled)
        self.record_