import sys
import os
import threading
import time
import torch
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QHBoxLayout, QFrame
)
from PyQt6.QtCore import QMetaObject, Q_ARG, QThread, pyqtSignal, Qt, QUrl, QSize, pyqtSlot
from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath
import speech_recognition as sr
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

from core.voice_util import play_cloned_voice
from core import gpt_core
from core.persona_process.kakao_cleaner import extract_user_messages
from core.persona_process.style_extractor import analyze_style, merge_analyses
from core.persona_process.persona_builder import build_persona
from core.persona_process.memory_extractor import extract_memory
from core.persona_process.memory_prompt_builder import build_memory_prompt
from core.persona_process.memory_store import load_memory, merge_memories, save_memory
from core.did_client import generate_avatar_video
from PyQt6.QtWidgets import QFileDialog
from core.persona_process.audio_extractor import extract_audio
from core.face_synthesizer import FaceSynthesizer

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

APP_STYLE = """
QWidget {
    background-color: #f0e8d8;
    color: #3a2810;
    font-family: 'Malgun Gothic', serif;
    font-size: 13px;
}
QPushButton {
    background-color: #e8d8b8;
    color: #3a2408;
    border: 1.5px solid #8a7050;
    border-radius: 6px;
    padding: 0px 12px;
    font-size: 12px;
    font-weight: 700;
    min-height: 34px;
}
QPushButton:hover { background-color: #d8c8a0; border-color: #6a5030; }
QPushButton:pressed { background-color: #c8b890; }
QPushButton:disabled { background-color: #e8e0d0; color: #b8a888; border-color: #c8b898; }

QPushButton#SendButton {
    background-color: #c8a060;
    color: #3a1e08;
    border: 1.5px solid #8a6030;
    border-radius: 8px;
    padding: 0px 20px;
    font-size: 13px;
    font-weight: 800;
    min-height: 42px;
    max-height: 42px;
}
QPushButton#SendButton:hover { background-color: #b89050; }

QPushButton#MicButton {
    background-color: #e8d8b8;
    color: #5a3e18;
    border: 1.5px solid #8a7050;
    border-radius: 8px;
    min-width: 42px; max-width: 42px;
    min-height: 42px; max-height: 42px;
    padding: 0;
    font-size: 15px;
}
QPushButton#MicButton:hover { background-color: #d8c8a0; }

QPushButton#LearnButton {
    background-color: #e8d8b8 !important;
    color: #3a2408 !important;
    border: 1.5px solid #8a7050;
    border-radius: 6px;
    padding: 0px 14px;
    font-size: 12px;
    font-weight: 800;
    min-height: 34px;
}
QPushButton#LearnButton:hover { background-color: #d8c8a0; color: #3a2408; }
QPushButton#LearnButton:disabled { background-color: #e8e0d0; color: #b8a888; }

QTextEdit#ChatOutput {
    background-color: #faf4ea;
    border: none;
    padding: 14px 16px;
    color: #3a2810;
    font-size: 13px;
    selection-background-color: #e8d4b0;
}
QLineEdit#ChatInput {
    background-color: #faf4ea;
    border: 1.5px solid #b09060;
    border-radius: 8px;
    padding: 10px 14px;
    color: #3a2810;
    font-size: 12px;
    selection-background-color: #e8d4b0;
    min-height: 42px;
    max-height: 42px;
}
QLineEdit#ChatInput:focus { border-color: #8a6840; }

QLineEdit#NameInput {
    background-color: #faf4ea;
    border: 1.5px solid #a08858;
    border-radius: 6px;
    padding: 4px 10px;
    color: #3a2810;
    font-size: 12px;
    min-height: 32px;
    max-height: 32px;
}
QLineEdit#NameInput:focus { border-color: #7a6038; }

QLabel#StatusLabel {
    color: #1a5e38;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 16px;
    background-color: #c8e8c8;
    border-top: 1.5px solid #b8c8a8;
}

QScrollBar:vertical { background: #f0e8d8; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #c8b898; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #a89068; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

LEFT_PANEL_STYLE  = "background-color: #ede0cc; border-right: 1.5px solid #b8a888;"
HEADER_STYLE      = "background-color: #e8dcc8; border-bottom: 1.5px solid #b8a888; border-top: none; border-left: none; border-right: none;"
AVATAR_AREA_STYLE = "background-color: #ede0cc;"
RIGHT_PANEL_STYLE = "background-color: #faf4ea;"
TOPBAR_STYLE      = "background-color: #d8c8a8; border-bottom: 1.5px solid #b8a888;"
SETUP_PANEL_STYLE = "background-color: #e0d0b0; border-bottom: 1.5px solid #b8a888;"
INPUT_AREA_STYLE  = "background-color: #e8dcc8; border-top: 1.5px solid #b8a888;"


class CircularPhotoLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap = None

    def setRoundedPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if not self._pixmap:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height()) - 24
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        path = QPainterPath()
        path.addEllipse(x, y, size, size)
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        px = x + (size - scaled.width()) // 2
        py = y + (size - scaled.height()) // 2
        painter.drawPixmap(px, py, scaled)
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#a09060"), 2))
        painter.drawEllipse(x, y, size, size)
        painter.setPen(QPen(QColor("#c0a870"), 1))
        painter.drawEllipse(x - 11, y - 11, size + 22, size + 22)


class GPTWorker(QThread):
    response_ready = pyqtSignal(str)

    def __init__(self, user_message, chat_history, system_prompt):
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
        self.setWindowTitle("SoulLink — AI Memorial Chatbot")
        self.setGeometry(100, 100, 1240, 800)
        self.setStyleSheet(APP_STYLE)

        self.chat_history = []
        self.auto_voice_enabled = True
        self.persona_name = "홍길동"
        self.kakao_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sample.txt"
        )
        self.avatar_photo_url = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data", "persona", "photo.jpg"
        )

        self.init_ui()
        self._load_persona_data()

    def init_ui(self):
        main_hbox = QHBoxLayout(self)
        main_hbox.setContentsMargins(0, 0, 0, 0)
        main_hbox.setSpacing(0)

        # ─────────────────────────────────────
        # 왼쪽: 제목 + 아바타
        # ─────────────────────────────────────
        left_panel = QWidget()
        left_panel.setStyleSheet(LEFT_PANEL_STYLE)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 왼쪽 상단: 제목 헤더
        title_widget = QWidget()
        title_widget.setStyleSheet(HEADER_STYLE)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 14, 18, 10)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title_label = QLabel("✦  AI MEMORIAL CHATBOT")
        title_label.setStyleSheet(
            "color:#1a0e04; font-size:17px; font-weight:900; "
            "letter-spacing:3px; background:transparent; "
            "border: none;"
        )
        subtitle_label = QLabel("Powered by GPT  ·  ElevenLabs  ·  D-ID")
        subtitle_label.setStyleSheet(
            "color:#7a6040; font-size:11px; background:transparent; border:none;"
        )
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle_label)

        soullink_label = QLabel("SoulLink")
        soullink_label.setStyleSheet(
            "color:#7a5830; font-size:13px; font-weight:700; "
            "letter-spacing:4px; font-style:italic; background:transparent; border:none;"
        )
        soullink_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        title_layout.addLayout(title_col)
        title_layout.addStretch()
        title_layout.addWidget(soullink_label)

        # 아바타 영역
        avatar_area = QWidget()
        avatar_area.setStyleSheet(AVATAR_AREA_STYLE)
        avatar_layout = QVBoxLayout(avatar_area)
        avatar_layout.setContentsMargins(20, 16, 20, 12)
        avatar_layout.setSpacing(10)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFixedSize(QSize(260, 260))

        self.photo_label = CircularPhotoLabel()
        self.photo_label.setStyleSheet("background-color: #e0d0a8; border-radius: 130px;")
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #e0d0a8; border-radius: 130px;")

        self.stacked_widget.addWidget(self.photo_label)
        self.stacked_widget.addWidget(self.video_widget)
        self.stacked_widget.setCurrentIndex(0)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

        tags_widget = QWidget()
        tags_widget.setStyleSheet("background: transparent;")
        tags_layout = QHBoxLayout(tags_widget)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(6)
        tags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for tag_text in ["따뜻한 목소리", "소중한 기억", "잊지 못할 미소"]:
            tag = QLabel(tag_text)
            tag.setStyleSheet("""
                background-color: #e8d8b0; color: #5a3a10;
                border: 1px solid #a08848; border-radius: 12px;
                padding: 4px 12px; font-size: 11px; font-weight: 600;
            """)
            tags_layout.addWidget(tag)

        avatar_layout.addStretch(1)
        avatar_layout.addWidget(self.stacked_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(tags_widget)
        avatar_layout.addStretch(1)

        # 상태 라벨 (왼쪽 패널 맨 아래)
        self.status_label = QLabel("⬤  시스템 준비 중...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setFixedHeight(30)

        left_layout.addWidget(title_widget)
        left_layout.addWidget(avatar_area, stretch=1)
        left_layout.addWidget(self.status_label)

        # ─────────────────────────────────────
        # 오른쪽: 버튼 + 설정 + 채팅
        # ─────────────────────────────────────
        right_panel = QWidget()
        right_panel.setStyleSheet(RIGHT_PANEL_STYLE)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 오른쪽 상단: 버튼 바
        topbar_widget = QWidget()
        topbar_widget.setStyleSheet(TOPBAR_STYLE)
        topbar_layout = QHBoxLayout(topbar_widget)
        topbar_layout.setContentsMargins(12, 8, 12, 8)
        topbar_layout.setSpacing(6)
        topbar_layout.addStretch(1)

        self.multi_upload_btn = QPushButton("📷  사진 다중 선택")
        self.synth_run_btn    = QPushButton("🔮  정면 합성 시작")
        self.upload_btn       = QPushButton("🎬  음성 추출")

        for btn in [self.multi_upload_btn, self.synth_run_btn, self.upload_btn]:
            btn.setFixedHeight(34)
            topbar_layout.addWidget(btn)

        # 설정 패널
        setup_widget = QWidget()
        setup_widget.setStyleSheet(SETUP_PANEL_STYLE)
        setup_layout = QVBoxLayout(setup_widget)
        setup_layout.setContentsMargins(14, 10, 14, 10)
        setup_layout.setSpacing(8)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel("👤 대상 이름")
        name_label.setStyleSheet(
            "color:#3a2408; font-size:12px; font-weight:700; "
            "background:transparent; min-width:76px;"
        )
        self.name_input = QLineEdit(self.persona_name)
        self.name_input.setObjectName("NameInput")
        self.name_input.setPlaceholderText("예: 홍길동")
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_input)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        file_label = QLabel("💬 대화 파일")
        file_label.setStyleSheet(
            "color:#3a2408; font-size:12px; font-weight:700; "
            "background:transparent; min-width:76px;"
        )
        self.file_name_label = QLabel(os.path.basename(self.kakao_file_path))
        self.file_name_label.setStyleSheet(
            "color:#6a4e28; font-size:11px; font-style:italic; background:transparent;"
        )
        self.file_select_btn = QPushButton("📂  파일 선택")
        self.file_select_btn.setFixedHeight(34)
        self.learn_btn = QPushButton("▶  학습 시작")
        self.learn_btn.setObjectName("LearnButton")
        self.learn_btn.setFixedHeight(34)
        file_row.addWidget(file_label)
        file_row.addWidget(self.file_name_label, stretch=1)
        file_row.addWidget(self.file_select_btn)
        file_row.addWidget(self.learn_btn)

        setup_layout.addLayout(name_row)
        setup_layout.addLayout(file_row)

        # 채팅 출력창
        self.chat_output = QTextEdit()
        self.chat_output.setObjectName("ChatOutput")
        self.chat_output.setReadOnly(True)

        # 입력 영역
        input_area = QWidget()
        input_area.setStyleSheet(INPUT_AREA_STYLE)
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(14, 10, 14, 10)
        input_layout.setSpacing(8)

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("그리운 마음을 전해보세요...")

        self.voice_record_button = QPushButton("🎤")
        self.voice_record_button.setObjectName("MicButton")
        self.voice_record_button.setFixedSize(42, 42)

        self.send_button = QPushButton("전송  ›")
        self.send_button.setObjectName("SendButton")
        self.send_button.setFixedSize(90, 42)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.voice_record_button)
        input_layout.addWidget(self.send_button)

        right_layout.addWidget(topbar_widget)
        right_layout.addWidget(setup_widget)
        right_layout.addWidget(self.chat_output, stretch=1)
        right_layout.addWidget(input_area)

        # 메인 조립
        main_hbox.addWidget(left_panel, stretch=46)
        main_hbox.addWidget(right_panel, stretch=54)

        # 이벤트 연결
        self.multi_upload_btn.clicked.connect(self.upload_multi_photos)
        self.synth_run_btn.clicked.connect(self.run_face_synthesis)
        self.upload_btn.clicked.connect(self.handle_video_upload)
        self.file_select_btn.clicked.connect(self.select_kakao_file)
        self.learn_btn.clicked.connect(self.start_learning)
        self.send_button.clicked.connect(
            lambda: self.send_message(self.chat_input.text().strip()))
        self.chat_input.returnPressed.connect(
            lambda: self.send_message(self.chat_input.text().strip()))
        self.voice_record_button.clicked.connect(self.listen_and_send)

        fal_key = os.getenv("FAL_KEY")
        self.face_synth = FaceSynthesizer(api_key=fal_key)
        self.multi_angle_paths = []
        self._update_photo_label()
        self._append_date_divider("기억의 문이 열렸습니다")

    # ─────────────────────────────────────
    # 헬퍼
    # ─────────────────────────────────────
    def _set_status(self, text, color="#1a5e38", bg="#c8e8c8"):
        self.status_label.setText(f"⬤  {text}")
        self.status_label.setStyleSheet(
            f"color:{color}; font-size:12px; font-weight:700; "
            f"padding:6px 16px; background-color:{bg}; "
            f"border-top:1.5px solid #b8c8a8;"
        )

    def _append_date_divider(self, text):
        self.chat_output.append(
            f"<div style='text-align:center; margin:12px 0 8px;'>"
            f"<span style='font-size:10px; color:#9a8060; font-style:italic; "
            f"letter-spacing:1.5px;'>— {text} —</span></div>"
        )

    def _append_user_msg(self, text):
        self.chat_output.append(
            f"<table width='100%' cellspacing='0' cellpadding='6'>"
            f"<tr><td align='right'>"
            f"<table cellspacing='0' cellpadding='0'><tr><td "
            f"style='background:#d4b878; color:#2a1408; "
            f"border:none; border-radius:16px 16px 4px 16px; "
            f"padding:10px 15px 10px 15px; font-size:13px; "
            f"line-height:1.7; max-width:300px;'>"
            f"<div style='font-size:10px; color:#7a5020; "
            f"margin-bottom:8px; letter-spacing:1px; font-style:italic;'>나</div>"
            f"<div>{text}</div>"
            f"</td></tr></table>"
            f"</td></tr></table>"
        )

    def _append_ai_msg(self, text):
        name = self.persona_name
        self.chat_output.append(
            f"<table width='100%' cellspacing='0' cellpadding='6'>"
            f"<tr><td align='left'>"
            f"<table cellspacing='0' cellpadding='0'><tr><td "
            f"style='background:#ffffff; color:#3a2410; "
            f"border:none; border-radius:16px 16px 16px 4px; "
            f"padding:10px 15px 10px 15px; font-size:13px; "
            f"line-height:1.7; max-width:300px;'>"
            f"<div style='font-size:10px; color:#8a6030; "
            f"margin-bottom:8px; letter-spacing:1px; font-style:italic; font-weight:700;'>{name}</div>"
            f"<div>{text}</div>"
            f"</td></tr></table>"
            f"</td></tr></table>"
        )

    @pyqtSlot(str)
    def _show_ai_msg(self, text: str):
        self._append_ai_msg(text)
        self.chat_output.ensureCursorVisible()
        self._set_status("답변 중...")

    # ─────────────────────────────────────
    # 파일 선택 & 학습
    # ─────────────────────────────────────
    def select_kakao_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "카카오톡 대화 파일 선택", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.kakao_file_path = path
            self.file_name_label.setText(os.path.basename(path))
            self._set_status(f"파일 선택됨: {os.path.basename(path)}", "#7a5020", "#f0e0b8")

    def start_learning(self):
        name = self.name_input.text().strip()
        if not name:
            self._set_status("대상 이름을 입력해주세요", "#8a2010", "#f8d8c8")
            return
        if not os.path.exists(self.kakao_file_path):
            self._set_status("대화 파일을 선택해주세요", "#8a2010", "#f8d8c8")
            return
        save_memory({"likes": [], "dislikes": [], "habits": [], "facts": []})

        self.persona_name = name
        self.learn_btn.setEnabled(False)
        self._set_status("기억을 불러오는 중...", "#7a5020", "#f0e0b8")
        threading.Thread(target=self._run_learning, daemon=True).start()

        self.persona_name = name
        self.learn_btn.setEnabled(False)
        self._set_status("기억을 불러오는 중...", "#7a5020", "#f0e0b8")
        threading.Thread(target=self._run_learning, daemon=True).start()

    def _run_learning(self):
        try:
            msgs = extract_user_messages(self.kakao_file_path, self.persona_name)
            print(f"DEBUG - 추출된 메시지 수: {len(msgs)}")       # ← 추가
            print(f"DEBUG - 첫 메시지: {msgs[:3] if msgs else '없음'}")  # ← 추가
            analyses = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            memory_chunks = extract_memory(msgs, client)
            existing_memory = load_memory()
            updated_memory = merge_memories(existing_memory, memory_chunks)
            save_memory(updated_memory)
            memory_prompt = build_memory_prompt(updated_memory)
            self.full_system_prompt = f"{self.persona_prompt}\n\n[기억]\n{memory_prompt}"
            QMetaObject.invokeMethod(self, "_on_learning_done",
                                     Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            QMetaObject.invokeMethod(self, "_on_learning_error",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, str(e)))

    @pyqtSlot()
    def _on_learning_done(self):
        self._set_status(f"기억 복원 완료 · {self.persona_name}과(와) 연결됨")
        self.learn_btn.setEnabled(True)
        self.chat_output.clear()
        self.chat_history.clear()
        self._append_date_divider(f"{self.persona_name}의 기억이 복원되었습니다")

    @pyqtSlot(str)
    def _on_learning_error(self, error_msg):
        self._set_status(f"오류: {error_msg}", "#8a2010", "#f8d8c8")
        self.learn_btn.setEnabled(True)

    def _load_persona_data(self):
        try:
            self._set_status("기억을 불러오는 중...", "#7a5020", "#f0e0b8")
            QApplication.processEvents()
            msgs = extract_user_messages(self.kakao_file_path, self.persona_name)
            analyses = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            memory_chunks = extract_memory(msgs, client)
            existing_memory = load_memory()
            updated_memory = merge_memories(existing_memory, memory_chunks)
            save_memory(updated_memory)
            memory_prompt = build_memory_prompt(updated_memory)
            self.full_system_prompt = f"{self.persona_prompt}\n\n[기억]\n{memory_prompt}"
            self._set_status(f"기억 복원 완료 · {self.persona_name}과(와) 연결됨")
        except Exception as e:
            self._set_status(f"오류: {str(e)}", "#8a2010", "#f8d8c8")

    # ─────────────────────────────────────
    # 대화
    # ─────────────────────────────────────
    def send_message(self, text):
        if not text or not hasattr(self, 'full_system_prompt'):
            return
        self._append_user_msg(text)
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": text})
        self._set_status("기억 속에서 답을 찾는 중...", "#7a5020", "#f0e0b8")
        self.worker = GPTWorker(text, self.chat_history, self.full_system_prompt)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.start()

    def handle_video_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "음성 추출용 영상 선택", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if file_path:
            self._set_status("음원 추출 중...", "#7a5020", "#f0e0b8")
            mp3_path = extract_audio(file_path)
            if mp3_path:
                self._set_status(f"추출 완료: {os.path.basename(mp3_path)}")
                import subprocess
                subprocess.Popen(f'explorer /select,"{os.path.abspath(mp3_path)}"')

    def handle_response(self, response):
        self._set_status("영상과 목소리를 준비 중입니다...", "#7a5020", "#f0e0b8")
        threading.Thread(target=self.run_did_clone, args=(response,), daemon=True).start()

    def run_did_clone(self, text):
        video_url = generate_avatar_video(text, self.avatar_photo_url)
        if video_url:
            self.chat_history.append({"role": "assistant", "content": text})
            QMetaObject.invokeMethod(self, "_show_ai_msg",
                Qt.ConnectionType.QueuedConnection, Q_ARG(str, text))
            self.media_player.setSource(QUrl(video_url))
            QMetaObject.invokeMethod(self.stacked_widget, "setCurrentIndex",
                Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
            QMetaObject.invokeMethod(self.media_player, "play",
                Qt.ConnectionType.QueuedConnection)
            time.sleep(1.5)
            if self.auto_voice_enabled:
                threading.Thread(target=play_cloned_voice, args=(text,), daemon=True).start()
        else:
            self.chat_output.append(
                "<div style='text-align:center; color:#8a2010; font-size:11px; "
                "margin:6px 0;'>— 영상 생성에 실패했습니다 —</div>"
            )
            self._set_status("영상 생성 실패", "#8a2010", "#f8d8c8")

    def listen_and_send(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self._set_status("듣고 있습니다...", "#7a5020", "#f0e0b8")
            QApplication.processEvents()
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=5)
                user_text = recognizer.recognize_google(audio, language='ko-KR')
                self.send_message(user_text)
            except Exception:
                self._set_status("음성 인식 실패", "#8a2010", "#f8d8c8")

    def upload_multi_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "학습용 사진 선택 (여러 장 가능)", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if files:
            self.multi_angle_paths = files
            self._set_status(f"{len(files)}장 선택됨", "#7a5020", "#f0e0b8")
            print(f"선택된 파일들: {files}")

    def run_face_synthesis(self):
        if not self.multi_angle_paths:
            self._set_status("먼저 사진들을 업로드해주세요", "#8a2010", "#f8d8c8")
            return
        self._set_status("얼굴 기억을 복원하는 중...", "#7a5020", "#f0e0b8")
        self.synth_run_btn.setEnabled(False)

        def worker():
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "data", "persona"
            )
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "photo.jpg")
            result = self.face_synth.synthesize(
                image_paths=self.multi_angle_paths,
                output_path=output_path
            )
            if result:
                self.avatar_photo_url = result
                self.current_persona_image = result
                if os.path.exists(result):
                    self._update_photo_label()
                QMetaObject.invokeMethod(self, "_on_synth_done",
                                         Qt.ConnectionType.QueuedConnection)
            else:
                QMetaObject.invokeMethod(self, "_on_synth_fail",
                                         Qt.ConnectionType.QueuedConnection)
            self.synth_run_btn.setEnabled(True)

        threading.Thread(target=worker, daemon=True).start()

    @pyqtSlot()
    def _on_synth_done(self):
        self._set_status("얼굴 기억 복원 완료")

    @pyqtSlot()
    def _on_synth_fail(self):
        self._set_status("복원 실패. 사진을 다시 확인하세요", "#8a2010", "#f8d8c8")

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.setSource(QUrl())
            self.stacked_widget.setCurrentIndex(0)
            self._update_photo_label()
            self._set_status(f"기억 복원 완료 · {self.persona_name}과(와) 연결됨")

    def _update_photo_label(self):
        if os.path.exists(self.avatar_photo_url):
            pixmap = QPixmap(self.avatar_photo_url)
            self.photo_label.setRoundedPixmap(pixmap)
        else:
            self.photo_label.setText("사진을 추가해주세요")
            self.photo_label.setStyleSheet(
                "background-color:#e0d0a8; color:#9a8060; "
                "font-size:12px; border-radius:130px;"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AIChatBotGUI()
    gui.show()
    sys.exit(app.exec())