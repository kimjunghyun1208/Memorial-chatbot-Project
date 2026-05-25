# ==========================================================
# 파일: src/app_gui.py
# 역할: SoulLink 메인 GUI
# ==========================================================

import sys
import os
import threading
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QHBoxLayout, QFrame,
    QStackedWidget, QFileDialog
)
from PyQt6.QtCore import QMetaObject, Q_ARG, QThread, pyqtSignal, Qt, QUrl, QSize, pyqtSlot
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath
import speech_recognition as sr
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

from core.voice_util import play_cloned_voice, create_voice_clone, save_voice_id_to_env
from core import gpt_core
from core.persona_process.kakao_cleaner         import extract_user_messages
from core.persona_process.style_extractor       import analyze_style, merge_analyses
from core.persona_process.persona_builder       import build_persona
from core.persona_process.memory_extractor      import extract_memory
from core.persona_process.memory_prompt_builder import build_memory_prompt
from core.persona_process.memory_store          import load_memory, merge_memories, save_memory
from core.did_client                            import generate_avatar_video
from core.persona_process.audio_extractor       import extract_audio
from core.face_synthesizer                      import FaceSynthesizer
from themes import (
    get_theme,
    INDIGO_APP_STYLE, INDIGO_PANELS,
    SAGE_APP_STYLE,   SAGE_PANELS
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

APP_STYLE, _PANELS = get_theme()
LEFT_PANEL_STYLE  = _PANELS["left"]
HEADER_STYLE      = _PANELS["header"]
AVATAR_AREA_STYLE = _PANELS["avatar"]
RIGHT_PANEL_STYLE = _PANELS["right"]
TOPBAR_STYLE      = _PANELS["topbar"]
SETUP_PANEL_STYLE = _PANELS["setup"]
INPUT_AREA_STYLE  = _PANELS["input"]

TEAL_LEFT_PANEL  = INDIGO_PANELS["left"]
TEAL_HEADER      = INDIGO_PANELS["header"]
TEAL_AVATAR      = INDIGO_PANELS["avatar"]
TEAL_RIGHT_PANEL = INDIGO_PANELS["right"]
TEAL_TOPBAR      = INDIGO_PANELS["topbar"]
TEAL_SETUP_PANEL = INDIGO_PANELS["setup"]
TEAL_INPUT_AREA  = INDIGO_PANELS["input"]

GOLD_LEFT_PANEL  = SAGE_PANELS["left"]
GOLD_HEADER      = SAGE_PANELS["header"]
GOLD_AVATAR      = SAGE_PANELS["avatar"]
GOLD_RIGHT_PANEL = SAGE_PANELS["right"]
GOLD_TOPBAR      = SAGE_PANELS["topbar"]
GOLD_SETUP_PANEL = SAGE_PANELS["setup"]
GOLD_INPUT_AREA  = SAGE_PANELS["input"]

# ──────────────────────────────────────────────────────────
# 설정 패널 라벨 스타일 — 테마별 분리
# ──────────────────────────────────────────────────────────
# indigo 테마: 짙은 청록 계열
_INDIGO_LABEL_STYLE     = "color:#0a2828; font-size:12px; font-weight:700; background:transparent; min-width:76px;"
_INDIGO_AGE_LABEL_STYLE = "color:#3a2408; font-size:12px; font-weight:700; background:transparent;"

# sage 테마: 밝은 회색 (다크 배경에서 잘 보이도록)
_SAGE_LABEL_STYLE       = "color:#a0a0a0; font-size:12px; font-weight:700; background:transparent; min-width:76px;"
_SAGE_AGE_LABEL_STYLE   = "color:#a0a0a0; font-size:12px; font-weight:700; background:transparent;"

# ──────────────────────────────────────────────────────────
# 사진 삭제 버튼 스타일 — 테마별 분리
# ──────────────────────────────────────────────────────────
# indigo 테마: 기존 청록 계열
_INDIGO_DELETE_BTN = """
    QPushButton {
        background-color: #b0d0c8;
        color: #0a2828;
        border: 1.5px solid #609898;
        border-radius: 6px;
        padding: 0px 12px;
        font-size: 12px;
        font-weight: 700;
        min-height: 34px;
    }
    QPushButton:hover    { background-color: #98c0b8; border-color: #407878; }
    QPushButton:disabled { background-color: #d0e8e8; color: #88b0b0; }
"""
# sage 테마: 차콜 계열
_SAGE_DELETE_BTN = """
    QPushButton {
        background-color: #2a2a2a;
        color: #909090;
        border: 1.5px solid #505050;
        border-radius: 6px;
        padding: 0px 12px;
        font-size: 12px;
        font-weight: 700;
        min-height: 34px;
    }
    QPushButton:hover    { background-color: #383838; border-color: #707070; }
    QPushButton:disabled { background-color: #1e1e1e; color: #484848; }
"""


class CircularPhotoLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap = None
        self._border_inner = "#8080b8"
        self._border_outer = "#5050a0"

    def setThemeBorder(self, inner: str, outer: str):
        self._border_inner = inner
        self._border_outer = outer
        self.update()

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
        x = (self.width()  - size) // 2
        y = (self.height() - size) // 2
        path = QPainterPath()
        path.addEllipse(x, y, size, size)
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        px = x + (size - scaled.width())  // 2
        py = y + (size - scaled.height()) // 2
        painter.drawPixmap(px, py, scaled)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(self._border_inner), 2))
        painter.drawEllipse(x, y, size, size)
        painter.setPen(QPen(QColor(self._border_outer), 1))
        painter.drawEllipse(x - 11, y - 11, size + 22, size + 22)


class GPTWorker(QThread):
    response_ready = pyqtSignal(str)

    def __init__(self, user_message, chat_history, system_prompt):
        super().__init__()
        self.user_message  = user_message
        self.chat_history  = chat_history
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

        self.chat_history       = []
        self.auto_voice_enabled = True

        _data_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_path = os.path.join(_data_root, "data", "memory", "settings.json")
        self.chat_log_path = os.path.join(_data_root, "data", "memory", "chat_log.json")
        self.backup_dir    = os.path.join(_data_root, "data", "memory", "backup")

        saved = self._load_settings()
        self.persona_name    = saved.get("persona_name", "홍길동")
        self.kakao_file_path = saved.get("kakao_file_path", os.path.join(
            _data_root, "data", "sample.txt"
        ))
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

        from themes import get_theme, ACTIVE_THEME
        _, _cur_panels = get_theme()

        # ══════════════════════════════════════════
        # 왼쪽 패널
        # ══════════════════════════════════════════
        left_panel = QWidget()
        left_panel.setStyleSheet(LEFT_PANEL_STYLE)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 헤더
        title_widget = QWidget()
        title_widget.setStyleSheet(HEADER_STYLE)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 14, 18, 10)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        if ACTIVE_THEME == "sage":
            title_text    = "✦  AI MEMORIAL CHATBOT"
            subtitle_text = "Powered by GPT  ·  ElevenLabs  ·  D-ID"
        else:
            title_text    = "✦  AI CHATBOT ASSISTANT"
            subtitle_text = "Powered by GPT  ·  ElevenLabs  ·  D-ID"

        title_label = QLabel(title_text)
        title_label.setStyleSheet(
            f"color:{_cur_panels['title_color']}; font-size:16px; font-weight:900; "
            f"letter-spacing:2px; background:transparent; border:none;"
        )
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setStyleSheet(
            f"color:{_cur_panels['subtitle_color']}; font-size:11px; "
            f"background:transparent; border:none;"
        )
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle_label)

        soullink_label = QLabel("SoulLink")
        soullink_label.setStyleSheet(
            f"color:{_cur_panels['soullink_color']}; font-size:13px; font-weight:700; "
            f"letter-spacing:4px; font-style:italic; background:transparent; border:none;"
        )
        soullink_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self._tag_border = _cur_panels.get("msg_ai_border", "#a08848")
        self._tag_color  = _cur_panels.get("msg_ai_color",  "#1a3820")

        self._help_btn = QPushButton("?")
        self._help_btn.setFixedSize(26, 26)
        self._help_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #a0a0d0;
                border: 1.5px solid #a0a0d0; border-radius: 13px;
                font-size: 13px; font-weight: 900; padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(160,160,208,0.25);
                color: #d0d0ff; border-color: #d0d0ff;
            }
        """)
        self._help_btn.clicked.connect(self._toggle_help)

        # 테마 토글 버튼 — 클릭 시 indigo ↔ sage 수동 전환
        self._theme_btn = QPushButton("◐")
        self._theme_btn.setFixedSize(26, 26)
        self._theme_btn.setToolTip("테마 전환 (밝은 ↔ 어두운)")
        self._theme_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #a0a0d0;
                border: 1.5px solid #a0a0d0; border-radius: 13px;
                font-size: 13px; font-weight: 900; padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(160,160,208,0.25);
                color: #d0d0ff; border-color: #d0d0ff;
            }
        """)
        self._theme_btn.clicked.connect(self._toggle_theme)

        title_layout.addLayout(title_col)
        title_layout.addStretch()
        title_layout.addWidget(self._theme_btn)
        title_layout.addSpacing(6)
        title_layout.addWidget(self._help_btn)
        title_layout.addSpacing(8)
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

        # 아바타 배경 — 시작 테마에 맞는 색으로 초기화
        _avatar_bg = _cur_panels.get("photo", "background-color: #c8cce8; border-radius: 130px;")
        self.photo_label = CircularPhotoLabel()
        self.photo_label.setStyleSheet(_avatar_bg)
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet(_avatar_bg)

        self.stacked_widget.addWidget(self.photo_label)
        self.stacked_widget.addWidget(self.video_widget)
        self.stacked_widget.setCurrentIndex(0)

        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

        tags_widget = QWidget()
        tags_widget.setStyleSheet("background: transparent;")
        self._tags_layout = QHBoxLayout(tags_widget)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(6)
        self._tags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar_layout.addStretch(1)
        avatar_layout.addWidget(self.stacked_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(tags_widget)
        avatar_layout.addStretch(1)

        self.status_label = QLabel("⬤  시스템 준비 중...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setFixedHeight(30)

        left_layout.addWidget(title_widget)
        left_layout.addWidget(avatar_area, stretch=1)
        left_layout.addWidget(self.status_label)

        # 헬프 오버레이
        self._help_overlay = QWidget(left_panel)
        self._help_overlay.setStyleSheet("""
            QWidget {
                background-color: #12123a; border: 1.5px solid #5050a0;
                border-radius: 14px;
            }
        """)
        self._help_overlay.setGeometry(10, 68, 358, 590)
        self._help_overlay.setVisible(False)

        help_inner = QVBoxLayout(self._help_overlay)
        help_inner.setContentsMargins(18, 14, 18, 14)
        help_inner.setSpacing(8)

        help_header_row = QHBoxLayout()
        help_title_lbl = QLabel("📋  사용 방법")
        help_title_lbl.setStyleSheet(
            "color:#e0e0ff; font-size:14px; font-weight:900; "
            "background:transparent; border:none; letter-spacing:2px;"
        )
        help_close_btn = QPushButton("✕")
        help_close_btn.setFixedSize(24, 24)
        help_close_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#8080c0; border:none;
                          font-size:14px; font-weight:900; }
            QPushButton:hover { color:#ffffff; }
        """)
        help_close_btn.clicked.connect(self._toggle_help)
        help_header_row.addWidget(help_title_lbl)
        help_header_row.addStretch()
        help_header_row.addWidget(help_close_btn)

        help_divider = QFrame()
        help_divider.setFrameShape(QFrame.Shape.HLine)
        help_divider.setStyleSheet("background-color:#3a3a80; border:none; max-height:1px;")

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("""
            QTextEdit { background:transparent; border:none; color:#b8b8e8; font-size:12px;
                        selection-background-color:#3a3a80; }
            QScrollBar:vertical { background:#1a1a50; width:4px; border-radius:2px; }
            QScrollBar::handle:vertical { background:#5050a0; border-radius:2px; min-height:20px; }
            QScrollBar::handle:vertical:hover { background:#8080c0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)
        help_text.setHtml("""
<div style='line-height:1.85; font-family:Malgun Gothic,serif; color:#b8b8e8; font-size:12px;'>
<p style='color:#90b8ff; font-weight:700; font-size:13px; margin:0 0 6px 0;'>📁 필요한 파일</p>
<p style='margin:0 0 4px 0;'>• <b style='color:#e0e0ff;'>카카오톡 대화 파일</b> (.txt)<br>
&nbsp;&nbsp;카카오톡 앱 → 채팅방 → 더보기 → 대화 내보내기</p>
<p style='margin:0 0 4px 0;'>• <b style='color:#e0e0ff;'>사진</b> (.jpg / .png)<br>
&nbsp;&nbsp;정면이 포함된 여러 장 권장</p>
<p style='margin:0 0 12px 0;'>• <b style='color:#e0e0ff;'>목소리가 담긴 영상</b> (.mp4 / .mov)<br>
&nbsp;&nbsp;5분 이상, 조용한 환경 권장</p>
<div style='border-top:1px solid #2a2a70; margin:4px 0 10px 0;'></div>
<p style='color:#90b8ff; font-weight:700; font-size:13px; margin:0 0 6px 0;'>🚀 사용 순서</p>
<p style='margin:0 0 5px 0;'><b style='color:#e0e0ff;'>① 이름 입력</b><br>&nbsp;&nbsp;대상 이름 입력란에 이름 입력</p>
<p style='margin:0 0 5px 0;'><b style='color:#e0e0ff;'>② 대화 파일 선택 → 학습 시작</b><br>&nbsp;&nbsp;말투·기억·성격 자동 분석</p>
<p style='margin:0 0 5px 0;'><b style='color:#e0e0ff;'>③ 사진 다중 선택 → 정면 합성</b><br>&nbsp;&nbsp;나이 입력 후 합성 시작</p>
<p style='margin:0 0 5px 0;'><b style='color:#e0e0ff;'>④ 음성 추출</b><br>&nbsp;&nbsp;mp3 추출 + ElevenLabs 클론 생성</p>
<p style='margin:0 0 5px 0;'><b style='color:#e0e0ff;'>⑤ 동영상 분석</b> (선택)<br>&nbsp;&nbsp;대화·행동 패턴 추가 학습</p>
<p style='margin:0 0 12px 0;'><b style='color:#e0e0ff;'>⑥ 대화 시작</b><br>&nbsp;&nbsp;AI 영상·목소리로 답변</p>
<div style='border-top:1px solid #2a2a70; margin:4px 0 10px 0;'></div>
<p style='color:#90b8ff; font-weight:700; font-size:13px; margin:0 0 6px 0;'>⚙️ .env 필수 API 키</p>
<p style='font-family:Consolas,monospace; font-size:11px; color:#80e0a0;
          background:#0a0a28; padding:8px 10px; border-radius:6px; margin:0; line-height:2;'>
OPENAI_API_KEY<br>XI_API_KEY&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;← ElevenLabs<br>VOICE_ID<br>DID_API_KEY<br>FAL_KEY</p>
</div>
        """)

        help_inner.addLayout(help_header_row)
        help_inner.addWidget(help_divider)
        help_inner.addWidget(help_text)
        self._help_overlay.raise_()

        # ══════════════════════════════════════════
        # 오른쪽 패널
        # ══════════════════════════════════════════
        right_panel = QWidget()
        right_panel.setStyleSheet(RIGHT_PANEL_STYLE)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._left_panel   = left_panel
        self._right_panel  = right_panel
        self._title_widget = title_widget
        self._avatar_area  = avatar_area

        # 상단 버튼 바
        topbar_widget = QWidget()
        topbar_widget.setStyleSheet(TOPBAR_STYLE)
        topbar_layout = QHBoxLayout(topbar_widget)
        topbar_layout.setContentsMargins(12, 8, 12, 8)
        topbar_layout.setSpacing(6)
        topbar_layout.addStretch(1)
        self._topbar_widget = topbar_widget

        self.multi_upload_btn  = QPushButton("📷  사진 다중 선택")
        self.synth_run_btn     = QPushButton("🔮  정면 합성 시작")
        self.upload_btn        = QPushButton("🎬  음성 추출")
        self.analyze_video_btn = QPushButton("🧠  동영상 분석")
        self.delete_photo_btn  = QPushButton("🗑  사진 삭제")
        # 사진 삭제 버튼 — 시작 테마 기준 스타일 적용
        self.delete_photo_btn.setStyleSheet(_INDIGO_DELETE_BTN)

        age_label = QLabel("나이")
        # 나이 라벨 — 참조 저장 (테마 전환 시 색상 변경)
        self._age_label = age_label
        age_label.setStyleSheet(_INDIGO_AGE_LABEL_STYLE)

        self.age_input = QLineEdit()
        self.age_input.setObjectName("NameInput")
        self.age_input.setPlaceholderText("예: 25")
        self.age_input.setFixedWidth(60)
        self.age_input.setFixedHeight(34)

        for btn in [self.multi_upload_btn, self.synth_run_btn,
                    self.delete_photo_btn, self.upload_btn, self.analyze_video_btn]:
            btn.setFixedHeight(34)
            topbar_layout.addWidget(btn)
        topbar_layout.addWidget(age_label)
        topbar_layout.addWidget(self.age_input)

        # 설정 패널
        setup_widget = QWidget()
        setup_widget.setStyleSheet(SETUP_PANEL_STYLE)
        setup_layout = QVBoxLayout(setup_widget)
        setup_layout.setContentsMargins(14, 10, 14, 10)
        setup_layout.setSpacing(8)
        self._setup_widget = setup_widget

        # 이름 입력 행
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel("👤 대상 이름")
        # 이름 라벨 — 참조 저장 (테마 전환 시 색상 변경)
        self._name_label = name_label
        name_label.setStyleSheet(_INDIGO_LABEL_STYLE)
        self.name_input = QLineEdit(self.persona_name)
        self.name_input.setObjectName("NameInput")
        self.name_input.setPlaceholderText("예: 홍길동")
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_input)

        # 파일 선택 행
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        file_label = QLabel("💬 대화 파일")
        # 파일 라벨 — 참조 저장 (테마 전환 시 색상 변경)
        self._file_label = file_label
        file_label.setStyleSheet(_INDIGO_LABEL_STYLE)
        self.file_name_label = QLabel(os.path.basename(self.kakao_file_path))
        self.file_name_label.setStyleSheet(
            "color:#407878; font-size:11px; font-style:italic; background:transparent;"
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

        self.talk_mode_btn = QPushButton("✦  고인과 대화하기")
        self.talk_mode_btn.setObjectName("TalkButton")
        self.talk_mode_btn.setFixedHeight(38)
        self.talk_mode_btn.setVisible(False)

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
        self._input_area = input_area

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        from themes import get_theme, ACTIVE_THEME as _AT
        _, _p = get_theme()
        self.chat_input.setPlaceholderText(_p.get("chat_placeholder", "메시지를 입력하세요..."))

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

        main_hbox.addWidget(left_panel,  stretch=46)
        main_hbox.addWidget(right_panel, stretch=54)

        # 이벤트 연결
        self.multi_upload_btn.clicked.connect(self.upload_multi_photos)
        self.synth_run_btn.clicked.connect(self.run_face_synthesis)
        self.upload_btn.clicked.connect(self.handle_video_upload)
        self.analyze_video_btn.clicked.connect(self.handle_video_analysis)
        self.delete_photo_btn.clicked.connect(self.delete_photo)
        self.file_select_btn.clicked.connect(self.select_kakao_file)
        self.learn_btn.clicked.connect(self.start_learning)
        self.talk_mode_btn.clicked.connect(self.switch_to_talk_mode)
        self.send_button.clicked.connect(
            lambda: self.send_message(self.chat_input.text().strip()))
        self.chat_input.returnPressed.connect(
            lambda: self.send_message(self.chat_input.text().strip()))
        self.voice_record_button.clicked.connect(self.listen_and_send)

        fal_key = os.getenv("FAL_KEY")
        self.face_synth = FaceSynthesizer(api_key=fal_key)
        self.multi_angle_paths = []
        self._update_photo_label()

        from themes import get_theme, ACTIVE_THEME as _AT2
        _, _p2 = get_theme()
        self._append_date_divider(_p2.get("chat_open_msg", "시작되었습니다"))

        self._INDIGO_APP    = INDIGO_APP_STYLE
        self._INDIGO_PANELS = INDIGO_PANELS
        self._SAGE_APP      = SAGE_APP_STYLE
        self._SAGE_PANELS   = SAGE_PANELS

        self.rebuild_tags()

    def rebuild_tags(self):
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        _, _cur_panels = get_theme()

        if getattr(self, '_talk_mode_active', False):   # ← getattr로 안전하게 참조
            tag_texts = ["따뜻한 목소리", "소중한 기억", "잊지 못할 미소"]
        else:
            tag_texts = ["자연스러운 대화", "기억 기반 응답", "목소리 재현"]

        for text in tag_texts:
            tag = QLabel(text)
            tag.setStyleSheet(f"""
                background: transparent;
                color: {_cur_panels.get('msg_ai_color')};
                border: 1px solid {_cur_panels.get('msg_ai_border')};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            """)
            self._tags_layout.addWidget(tag)


    # ──────────────────────────────────────────────────────
    # 헬프 토글
    # ──────────────────────────────────────────────────────
    def _toggle_help(self):
        visible = self._help_overlay.isVisible()
        self._help_overlay.setVisible(not visible)
        if not visible:
            self._help_overlay.raise_()

    def _toggle_theme(self):
        """◐ 버튼 클릭 시 indigo ↔ sage 테마를 수동으로 전환한다."""
        if getattr(self, '_talk_mode_active', False):
            self.switch_to_setup_mode()
        else:
            self.switch_to_talk_mode()

    # ──────────────────────────────────────────────────────
    # 테마 전환
    # ──────────────────────────────────────────────────────
    def switch_to_talk_mode(self):
        if getattr(self, '_talk_mode_active', False):
            return
        self._talk_mode_active = True

        self.setStyleSheet(SAGE_APP_STYLE)
        self._left_panel.setStyleSheet(SAGE_PANELS["left"])
        self._title_widget.setStyleSheet(SAGE_PANELS["header"])
        self._avatar_area.setStyleSheet(SAGE_PANELS["avatar"])
        self._right_panel.setStyleSheet(SAGE_PANELS["right"])
        self._topbar_widget.setStyleSheet(SAGE_PANELS["topbar"])
        self._setup_widget.setStyleSheet(SAGE_PANELS["setup"])
        self._input_area.setStyleSheet(SAGE_PANELS["input"])
        self.photo_label.setThemeBorder("#505050", "#383838")
        self.photo_label.setStyleSheet(SAGE_PANELS["photo"])
        self.video_widget.setStyleSheet(SAGE_PANELS["photo"])

        # ── 설정 패널 라벨 → 밝은 회색으로 변경 ──────────
        self._name_label.setStyleSheet(_SAGE_LABEL_STYLE)
        self._file_label.setStyleSheet(_SAGE_LABEL_STYLE)
        self._age_label.setStyleSheet(_SAGE_AGE_LABEL_STYLE)

        # ── 사진 삭제 버튼 → 차콜 스타일로 변경 ──────────
        self.delete_photo_btn.setStyleSheet(_SAGE_DELETE_BTN)

        self._set_status(
            f"기억 복원 완료 · {self.persona_name}과(와) 연결됨",
            SAGE_PANELS["status_color"], SAGE_PANELS["status_bg"]
        )
        if self._help_overlay.isVisible():
            self._help_overlay.setVisible(False)
        self.rebuild_tags() #임시 코드 추가


    def switch_to_setup_mode(self):
        self._talk_mode_active = False

        self.setStyleSheet(INDIGO_APP_STYLE)
        self._left_panel.setStyleSheet(INDIGO_PANELS["left"])
        self._title_widget.setStyleSheet(INDIGO_PANELS["header"])
        self._avatar_area.setStyleSheet(INDIGO_PANELS["avatar"])
        self._right_panel.setStyleSheet(INDIGO_PANELS["right"])
        self._topbar_widget.setStyleSheet(INDIGO_PANELS["topbar"])
        self._setup_widget.setStyleSheet(INDIGO_PANELS["setup"])
        self._input_area.setStyleSheet(INDIGO_PANELS["input"])
        self.photo_label.setThemeBorder("#8080b8", "#5050a0")
        self.photo_label.setStyleSheet(INDIGO_PANELS["photo"])
        self.video_widget.setStyleSheet(INDIGO_PANELS["photo"])

        # ── 설정 패널 라벨 → 원래 인디고 스타일로 복원 ───
        self._name_label.setStyleSheet(_INDIGO_LABEL_STYLE)
        self._file_label.setStyleSheet(_INDIGO_LABEL_STYLE)
        self._age_label.setStyleSheet(_INDIGO_AGE_LABEL_STYLE)

        # ── 사진 삭제 버튼 → 원래 인디고 스타일로 복원 ───
        self.delete_photo_btn.setStyleSheet(_INDIGO_DELETE_BTN)

        self._set_status(
            "AI 어시스턴트 · 준비됨",
            INDIGO_PANELS["status_color"], INDIGO_PANELS["status_bg"]
        )

        self.rebuild_tags()

    # ──────────────────────────────────────────────────────
    # 설정 저장/불러오기
    # ──────────────────────────────────────────────────────
    def _load_settings(self) -> dict:
        import json
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 설정 불러오기 실패: {e}")
        return {}

    def _save_settings(self):
        import json
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump({
                    "persona_name":    self.persona_name,
                    "kakao_file_path": self.kakao_file_path
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 설정 저장 실패: {e}")

    # ──────────────────────────────────────────────────────
    # 대화 기록 백업/저장/불러오기
    # ──────────────────────────────────────────────────────
    def _backup_chat_log(self):
        import json
        from datetime import datetime
        if not self.chat_history:
            return
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(os.path.join(self.backup_dir, f"{self.persona_name}_{ts}.json"),
                      "w", encoding="utf-8") as f:
                json.dump({"persona_name": self.persona_name,
                           "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           "chat_history": self.chat_history},
                          f, ensure_ascii=False, indent=2)
            with open(os.path.join(self.backup_dir, f"{self.persona_name}_{ts}.txt"),
                      "w", encoding="utf-8") as f:
                f.write(f"대화 상대: {self.persona_name}\n\n")
                for item in self.chat_history:
                    role = "나" if item["role"] == "user" else self.persona_name
                    f.write(f"[{role}]\n{item['content']}\n\n")
        except Exception as e:
            print(f"⚠️ 대화 백업 실패: {e}")

    def _load_chat_log(self):
        import json
        if not os.path.exists(self.chat_log_path):
            self._append_date_divider("기억의 문이 열렸습니다")
            return
        try:
            with open(self.chat_log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("chat_history") and data.get("persona_name") == self.persona_name:
                self.chat_history = data["chat_history"]
                self._append_date_divider("이전 대화 기록")
                for html in data.get("display_html", []):
                    self.chat_output.append(html)
                self._append_date_divider("새 대화 시작")
            else:
                self._append_date_divider("기억의 문이 열렸습니다")
        except Exception as e:
            print(f"⚠️ 대화 기록 불러오기 실패: {e}")
            self._append_date_divider("기억의 문이 열렸습니다")

    def _save_chat_log(self):
        import json
        if not self.chat_history:
            return
        try:
            os.makedirs(os.path.dirname(self.chat_log_path), exist_ok=True)
            display_html = []
            for item in self.chat_history:
                if item["role"] == "user":
                    display_html.append(
                        f"<table width='100%' cellspacing='0' cellpadding='4'>"
                        f"<tr><td align='right'><table cellspacing='0' cellpadding='0'><tr><td "
                        f"style='background:#323232; color:#e0e0e0; border:none; "
                        f"border-radius:16px 16px 4px 16px; padding:10px 15px; "
                        f"font-size:13px; line-height:1.8; max-width:300px;'>"
                        f"<div style='font-size:10px; color:#909090; margin-bottom:8px; "
                        f"letter-spacing:1px; font-style:italic;'>나</div>"
                        f"<div>{item['content']}</div>"
                        f"</td></tr></table></td></tr></table>"
                    )
                else:
                    display_html.append(
                        f"<table width='100%' cellspacing='0' cellpadding='4'>"
                        f"<tr><td align='left'><table cellspacing='0' cellpadding='0'><tr><td "
                        f"style='background:#2a2a2a; color:#c8c8c8; border:none; "
                        f"border-radius:16px 16px 16px 4px; padding:10px 15px; "
                        f"font-size:13px; line-height:1.8; max-width:300px;'>"
                        f"<div style='font-size:10px; color:#787878; margin-bottom:8px; "
                        f"letter-spacing:1px; font-style:italic; font-weight:700;'>{self.persona_name}</div>"
                        f"<div>{item['content']}</div>"
                        f"</td></tr></table></td></tr></table>"
                    )
            with open(self.chat_log_path, "w", encoding="utf-8") as f:
                json.dump({"persona_name": self.persona_name,
                           "chat_history": self.chat_history,
                           "display_html": display_html},
                          f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 대화 기록 저장 실패: {e}")

    def closeEvent(self, event):
        self._save_chat_log()
        self._save_settings()
        self._backup_chat_log()
        event.accept()

    # ──────────────────────────────────────────────────────
    # UI 헬퍼
    # ──────────────────────────────────────────────────────
    def _set_status(self, text, color="#909090", bg="#161616"):
        self.status_label.setText(f"⬤  {text}")
        self.status_label.setStyleSheet(
            f"color:{color}; font-size:12px; font-weight:700; "
            f"padding:6px 16px; background-color:{bg}; "
            f"border-top:1.5px solid #323232;"
        )

    def _append_date_divider(self, text):
        self.chat_output.append(
            f"<div style='text-align:center; margin:12px 0 8px;'>"
            f"<span style='font-size:10px; color:#686868; font-style:italic; "
            f"letter-spacing:1.5px;'>— {text} —</span></div>"
        )

    def _append_user_msg(self, text):
        self.chat_output.append(
            f"<table width='100%' cellspacing='0' cellpadding='6'>"
            f"<tr><td align='right'><table cellspacing='0' cellpadding='0'><tr><td "
            f"style='background:#323232; color:#e0e0e0; border:none; "
            f"border-radius:16px 16px 4px 16px; "
            f"padding:10px 15px; font-size:13px; line-height:1.7; max-width:300px;'>"
            f"<div style='font-size:10px; color:#909090; "
            f"margin-bottom:8px; letter-spacing:1px; font-style:italic;'>나</div>"
            f"<div>{text}</div>"
            f"</td></tr></table></td></tr></table>"
        )

    def _append_ai_msg(self, text):
        name = self.persona_name
        self.chat_output.append(
            f"<table width='100%' cellspacing='0' cellpadding='6'>"
            f"<tr><td align='left'><table cellspacing='0' cellpadding='0'><tr><td "
            f"style='background:#2a2a2a; color:#c8c8c8; border:none; "
            f"border-radius:16px 16px 16px 4px; "
            f"padding:10px 15px; font-size:13px; line-height:1.7; max-width:300px;'>"
            f"<div style='font-size:10px; color:#787878; "
            f"margin-bottom:8px; letter-spacing:1px; font-style:italic; font-weight:700;'>{name}</div>"
            f"<div>{text}</div>"
            f"</td></tr></table></td></tr></table>"
        )

    @pyqtSlot(str)
    def _show_ai_msg(self, text: str):
        self._append_ai_msg(text)
        self.chat_output.ensureCursorVisible()
        self._set_status("답변 중...")

    @pyqtSlot(str, str, str)
    def _set_status_slot(self, text: str, color: str, bg: str):
        self._set_status(text, color, bg)

    # ──────────────────────────────────────────────────────
    # 학습
    # ──────────────────────────────────────────────────────
    def select_kakao_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "카카오톡 대화 파일 선택", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.kakao_file_path = path
            self.file_name_label.setText(os.path.basename(path))
            self._set_status(f"파일 선택됨: {os.path.basename(path)}", "#888888", "#1a1a1a")

    def start_learning(self):
        name = self.name_input.text().strip()
        if not name:
            self._set_status("대상 이름을 입력해주세요", "#888888", "#1a1a1a")
            return
        if not os.path.exists(self.kakao_file_path):
            self._set_status("대화 파일을 선택해주세요", "#888888", "#1a1a1a")
            return
        self.persona_name = name
        self.learn_btn.setEnabled(False)
        self._set_status("기억을 불러오는 중...", "#888888", "#1a1a1a")
        threading.Thread(target=self._run_learning, daemon=True).start()

    def _run_learning(self):
        try:
            msgs         = extract_user_messages(self.kakao_file_path, self.persona_name)
            analyses     = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            memory_chunks   = extract_memory(msgs, client)
            existing_memory = load_memory()
            updated_memory  = merge_memories(existing_memory, memory_chunks)
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
        self._set_status(
            f"기억 복원 완료 · {self.persona_name}과(와) 연결됨",
            SAGE_PANELS["status_color"], SAGE_PANELS["status_bg"]
        )
        self.learn_btn.setEnabled(True)
        self.chat_output.clear()
        self.chat_history.clear()
        if os.path.exists(self.chat_log_path):
            os.remove(self.chat_log_path)
        self._append_date_divider(f"{self.persona_name}의 기억이 복원되었습니다")

    @pyqtSlot(str)
    def _on_learning_error(self, error_msg):
        self._set_status(f"오류: {error_msg}", "#888888", "#1a1a1a")
        self.learn_btn.setEnabled(True)

    def _load_persona_data(self):
        try:
            self._set_status("기억을 불러오는 중...", "#888888", "#1a1a1a")
            QApplication.processEvents()
            msgs         = extract_user_messages(self.kakao_file_path, self.persona_name)
            analyses     = analyze_style(msgs)
            persona_json = merge_analyses(analyses)
            self.persona_prompt = build_persona(persona_json)
            memory_chunks   = extract_memory(msgs, client)
            existing_memory = load_memory()
            updated_memory  = merge_memories(existing_memory, memory_chunks)
            save_memory(updated_memory)
            memory_prompt = build_memory_prompt(updated_memory)
            self.full_system_prompt = f"{self.persona_prompt}\n\n[기억]\n{memory_prompt}"
            self._set_status(f"기억 복원 완료 · {self.persona_name}과(와) 연결됨")
        except Exception as e:
            self._set_status(f"오류: {str(e)}", "#888888", "#1a1a1a")

    # ──────────────────────────────────────────────────────
    # 대화
    # ──────────────────────────────────────────────────────
    def send_message(self, text):
        if not text or not hasattr(self, 'full_system_prompt'):
            return
        # 테마 자동 전환 제거 — 수동 토글 버튼으로만 변경 가능
        if len(self.chat_history) >= 20:
            self._set_status("대화 내용 요약 중...", "#888888", "#1a1a1a")
            QApplication.processEvents()
            summary = gpt_core.summarize_chat_history(self.chat_history)
            if summary:
                self.chat_history = [
                    {"role": "assistant", "content": f"[이전 대화 요약] {summary}"}
                ]
                self._append_date_divider("대화 내용이 요약되었습니다")
        self._append_user_msg(text)
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": text})
        self._set_status("기억 속에서 답을 찾는 중...", "#888888", "#1a1a1a")
        self.worker = GPTWorker(text, self.chat_history, self.full_system_prompt)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.start()

    def handle_response(self, response):
        self._set_status("영상과 목소리를 준비 중입니다...", "#888888", "#1a1a1a")
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
        else:
            self.chat_output.append(
                "<div style='text-align:center; color:#606060; font-size:11px; "
                "margin:6px 0;'>— 영상 생성에 실패했습니다 —</div>"
            )
            self._set_status("영상 생성 실패", "#888888", "#1a1a1a")

    # ──────────────────────────────────────────────────────
    # 미디어
    # ──────────────────────────────────────────────────────
    def handle_video_analysis(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "분석할 동영상 선택", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if not file_path:
            return
        self._set_status("동영상 분석 준비 중...", "#888888", "#1a1a1a")
        self.analyze_video_btn.setEnabled(False)
        threading.Thread(target=self._run_video_analysis, args=(file_path,), daemon=True).start()

    def _run_video_analysis(self, video_path):
        try:
            from core.video_analyzer import analyze_video
            QMetaObject.invokeMethod(self, "_set_status_slot",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "음성 인식 + 행동 분석 중... (수 분 소요)"),
                Q_ARG(str, "#888888"), Q_ARG(str, "#1a1a1a"))
            analyze_video(video_path, self.persona_name, client)
            QMetaObject.invokeMethod(self, "_on_video_analysis_done",
                Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            print(f"❌ 동영상 분석 오류: {e}")
            QMetaObject.invokeMethod(self, "_set_status_slot",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"분석 실패: {str(e)[:40]}"),
                Q_ARG(str, "#888888"), Q_ARG(str, "#1a1a1a"))
        finally:
            self.analyze_video_btn.setEnabled(True)

    @pyqtSlot()
    def _on_video_analysis_done(self):
        self._set_status(f"✅ 동영상 분석 완료! {self.persona_name}의 목소리·대화 학습됨")
        self._append_date_divider(f"{self.persona_name}의 동영상 기억이 추가되었습니다")

    def handle_video_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "음성 추출용 영상 선택", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if not file_path:
            return
        self._set_status("음원 추출 중...", "#888888", "#1a1a1a")
        threading.Thread(target=self._extract_and_clone, args=(file_path,), daemon=True).start()

    def _extract_and_clone(self, file_path):
        mp3_path = extract_audio(file_path)
        if not mp3_path:
            self._set_status("음원 추출 실패", "#888888", "#1a1a1a")
            return
        QMetaObject.invokeMethod(self, "_on_extract_done",
            Qt.ConnectionType.QueuedConnection, Q_ARG(str, mp3_path))
        voice_name = self.persona_name if hasattr(self, 'persona_name') else "cloned_voice"
        QMetaObject.invokeMethod(self, "_set_status_slot",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, f"'{voice_name}' 음성 클론 생성 중..."),
            Q_ARG(str, "#888888"), Q_ARG(str, "#1a1a1a"))
        voice_id = create_voice_clone(mp3_path, voice_name)
        if voice_id:
            save_voice_id_to_env(voice_id)
            QMetaObject.invokeMethod(self, "_on_clone_done",
                Qt.ConnectionType.QueuedConnection, Q_ARG(str, voice_id))
        else:
            QMetaObject.invokeMethod(self, "_set_status_slot",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "음성 클론 생성 실패. ElevenLabs 구독을 확인해주세요"),
                Q_ARG(str, "#888888"), Q_ARG(str, "#1a1a1a"))

    @pyqtSlot(str)
    def _on_extract_done(self, mp3_path):
        self._set_status(f"음원 추출 완료: {os.path.basename(mp3_path)}")
        import subprocess
        subprocess.Popen(f'explorer /select,"{os.path.abspath(mp3_path)}"')

    @pyqtSlot(str)
    def _on_clone_done(self, voice_id):
        self._set_status("✅ 음성 클론 완료! Voice ID 자동 저장됨")

    def listen_and_send(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self._set_status("듣고 있습니다...", "#888888", "#1a1a1a")
            QApplication.processEvents()
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=5)
                user_text = recognizer.recognize_google(audio, language='ko-KR')
                self.send_message(user_text)
            except Exception:
                self._set_status("음성 인식 실패", "#888888", "#1a1a1a")

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.setSource(QUrl())
            self.stacked_widget.setCurrentIndex(0)
            self._update_photo_label()
            self._set_status(f"기억 복원 완료 · {self.persona_name}과(와) 연결됨")

    # ──────────────────────────────────────────────────────
    # 사진
    # ──────────────────────────────────────────────────────
    def upload_multi_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "학습용 사진 선택 (여러 장 가능)", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if files:
            self.multi_angle_paths = files
            self._set_status(f"{len(files)}장 선택됨", "#888888", "#1a1a1a")

    def run_face_synthesis(self):
        if not self.multi_angle_paths:
            self._set_status("먼저 사진들을 업로드해주세요", "#888888", "#1a1a1a")
            return
        self._set_status("얼굴 기억을 복원하는 중...", "#888888", "#1a1a1a")
        self.synth_run_btn.setEnabled(False)
        self._show_loading_on_avatar()

        def worker():
            output_dir  = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "data", "persona"
            )
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "photo.jpg")
            age_text = self.age_input.text().strip()
            age = int(age_text) if age_text.isdigit() else None
            result = self.face_synth.synthesize(
                image_paths=self.multi_angle_paths,
                output_path=output_path,
                age=age
            )
            if result:
                self.avatar_photo_url      = result
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

    def delete_photo(self):
        from PyQt6.QtWidgets import QMessageBox
        if not os.path.exists(self.avatar_photo_url):
            self._set_status("삭제할 사진이 없습니다", "#888888", "#1a1a1a")
            return
        reply = QMessageBox.question(
            self, "사진 삭제",
            f"저장된 사진을 삭제하시겠습니까?\n{os.path.basename(self.avatar_photo_url)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.avatar_photo_url)
                self.multi_angle_paths = []
                self.photo_label.setRoundedPixmap(None)
                self.photo_label.setText("사진을 추가해주세요")
                if getattr(self, '_talk_mode_active', False):
                    self.photo_label.setStyleSheet(
                        "background-color:#2a2a2a; color:#686868; "
                        "font-size:12px; border-radius:130px;"
                    )
                else:
                    self.photo_label.setStyleSheet(
                        "background-color:#c8cce8; color:#6060a0; "
                        "font-size:12px; border-radius:130px;"
                    )
                self.stacked_widget.setCurrentIndex(0)
                self._set_status("사진이 삭제되었습니다", "#888888", "#1a1a1a")
            except Exception as e:
                self._set_status(f"삭제 실패: {e}", "#888888", "#1a1a1a")

    def _show_loading_on_avatar(self):
        # 테마에 따라 로딩 배경/글씨 색 분기
        if getattr(self, '_talk_mode_active', False):
            bg, fg = "#2e2e2e", "#909090"
        else:
            bg, fg = "#c0c4e0", "#5050a0"
        self.photo_label.setRoundedPixmap(None)
        self.photo_label.setText("⏳\n\n이미지 생성 중...\n잠시만 기다려주세요")
        self.photo_label.setStyleSheet(
            f"background-color:{bg}; color:{fg}; "
            "font-size:13px; font-weight:600; border-radius:130px; "
            "qproperty-alignment: AlignCenter;"
        )
        self.stacked_widget.setCurrentIndex(0)

    def _update_photo_label(self):
        if os.path.exists(self.avatar_photo_url):
            pixmap = QPixmap(self.avatar_photo_url)
            self.photo_label.setRoundedPixmap(pixmap)
        else:
            # 테마에 따라 안내 텍스트 배경/글씨 색 분기
            if getattr(self, '_talk_mode_active', False):
                bg, fg = "#2a2a2a", "#686868"
            else:
                bg, fg = "#c8cce8", "#6060a0"
            self.photo_label.setText("사진을 추가해주세요")
            self.photo_label.setStyleSheet(
                f"background-color:{bg}; color:{fg}; "
                "font-size:12px; border-radius:130px;"
            )

    @pyqtSlot()
    def _on_synth_done(self):
        self._set_status("얼굴 기억 복원 완료")

    @pyqtSlot()
    def _on_synth_fail(self):
        self._set_status("복원 실패. 사진을 다시 확인하세요", "#888888", "#1a1a1a")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AIChatBotGUI()
    gui.show()
    sys.exit(app.exec())