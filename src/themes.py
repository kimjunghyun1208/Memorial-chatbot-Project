# ============================================================
# 파일  : src/themes.py
# 역할  : SoulLink UI 테마(색상·스타일) 정의 및 반환
#
# 구성
#   [1] ACTIVE_THEME  — 시작 테마 선택 변수
#   [2] INDIGO 테마   — 기본/설정 모드용 QSS + 패널 색상
#   [3] SAGE 테마     — 고인 대화 모드용 QSS + 패널 색상 (다크 차콜)
#   [4] get_theme()   — 활성 테마 반환 함수
#
# 사용처 : app_gui.py 에서 get_theme() 호출
# ============================================================


# ────────────────────────────────────────────────────────────
# [1] 활성 테마 선택
#     "indigo" : 시작 테마  — 인디고 계열, 일반 AI 챗봇 느낌
#     "sage"   : 대화 테마  — 차콜 다크, 고요한 추모 분위기
#     ※ 대화 첫 메시지 전송 시 app_gui.py 가 자동으로 sage 전환
# ────────────────────────────────────────────────────────────
ACTIVE_THEME = "sage"


# ============================================================
# [2] INDIGO 테마  ─  인디고(파랑) + 골드
#     용도 : 기본 모드 / 설정·학습 진행 중 화면
# ============================================================

INDIGO_APP_STYLE = """
QWidget {
    background-color: #eef0f8;
    color: #1a1a5a;
    font-family: 'Malgun Gothic', serif;
    font-size: 13px;
}
QPushButton {
    background-color: #e0e0f4;
    color: #1a1a5a;
    border: 1.5px solid #8080b8;
    border-radius: 6px;
    padding: 0px 12px;
    font-size: 12px;
    font-weight: 700;
    min-height: 34px;
}
QPushButton:hover    { background-color: #d0d0ec; border-color: #5050a0; }
QPushButton:pressed  { background-color: #c0c0e0; }
QPushButton:disabled { background-color: #e8e8f4; color: #9090b8; border-color: #b0b0d0; }
QPushButton#SendButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3a3a9a, stop:1 #2a2a7a);
    color: #ffffff;
    border: 1.5px solid #2a2a7a;
    border-radius: 8px;
    padding: 0px 20px;
    font-size: 13px;
    font-weight: 800;
    min-height: 42px;
    max-height: 42px;
}
QPushButton#SendButton:hover { background-color: #2a2a8a; }
QPushButton#MicButton {
    background-color: #e0e0f4;
    color: #3a3a9a;
    border: 1.5px solid #8080b8;
    border-radius: 8px;
    min-width: 42px; max-width: 42px;
    min-height: 42px; max-height: 42px;
    padding: 0;
    font-size: 15px;
}
QPushButton#MicButton:hover { background-color: #d0d0ec; }
QPushButton#LearnButton {
    background-color: #e0e0f4 !important;
    color: #1a1a5a !important;
    border: 1.5px solid #8080b8;
    border-radius: 6px;
    padding: 0px 14px;
    font-size: 12px;
    font-weight: 800;
    min-height: 34px;
}
QPushButton#LearnButton:hover    { background-color: #d0d0ec; }
QPushButton#LearnButton:disabled { background-color: #e8e8f4; color: #9090b8; }
QTextEdit#ChatOutput {
    background-color: #f8f8ff;
    border: none;
    padding: 14px 16px;
    color: #1a1a5a;
    font-size: 13px;
    selection-background-color: #c0c0e8;
}
QLineEdit#ChatInput {
    background-color: #f8f8ff;
    border: 1.5px solid #8080b8;
    border-radius: 8px;
    padding: 10px 14px;
    color: #1a1a5a;
    font-size: 12px;
    selection-background-color: #c0c0e8;
    min-height: 42px;
    max-height: 42px;
}
QLineEdit#ChatInput:focus { border-color: #3a3a9a; }
QLineEdit#NameInput {
    background-color: #f8f8ff;
    border: 1.5px solid #8080b8;
    border-radius: 6px;
    padding: 4px 10px;
    color: #1a1a5a;
    font-size: 12px;
    min-height: 32px;
    max-height: 32px;
}
QLineEdit#NameInput:focus { border-color: #3a3a9a; }
QLabel#StatusLabel {
    color: #1a1a5a;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 16px;
    background-color: #d8d8f0;
    border-top: 1.5px solid #9090c0;
}
QScrollBar:vertical              { background: #eef0f8; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical      { background: #9090c0; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #6060a0; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical    { height: 0; }
"""

INDIGO_PANELS = {
    "left":     "background-color: #eef0f8; border-right: 1.5px solid #9090c0;",
    "header":   "background-color: #1a1a5a; border: none;",
    "avatar":   "background-color: #eef0f8;",
    "right":    "background-color: #f8f8ff;",
    "topbar":   "background-color: #e4e4f4; border-bottom: 1.5px solid #9090c0;",
    "setup":    "background-color: #eaecf8; border-bottom: 1.5px solid #9090c0;",
    "input":    "background-color: #e4e4f4; border-top: 1.5px solid #9090c0;",
    "photo":    "background-color: #c8cce8; border-radius: 130px;",
    "title_color":    "#f0f0ff",
    "subtitle_color": "#a0a0e0",
    "soullink_color": "#d4b870",
    "status_text":    "AI 어시스턴트 · 준비됨",
    "status_color":   "#1a1a5a",
    "status_bg":      "#d8d8f0",
    "chat_placeholder": "무엇이든 물어보세요...",
    "chat_open_msg":    "AI 어시스턴트가 준비되었습니다",
    "msg_ai_bg":     "#ffffff",
    "msg_ai_border": "#c0c0e0",
    "msg_ai_color":  "#1a1a5a",
    "msg_ai_name":   "#8080b8",
    "msg_user_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3a3a9a,stop:1 #2a2a7a)",
    "msg_user_color": "#f0f0ff",
    "msg_user_name":  "#a0a0e0",
}


# ============================================================
# [3] SAGE 테마  ─  다크 차콜 (고요한 추모 분위기)
#
#     명도 계층 (밝을수록 앞으로 나옴)
#       #111111  헤더 (가장 어두운 강조)
#       #1a1a1a  왼쪽 패널 배경
#       #1e1e1e  오른쪽 채팅 배경
#       #222222  버튼 바 / 입력 영역
#       #262626  설정 패널
#       #2e2e2e  버튼 배경
#       #383838  버튼 hover / 테두리
# ============================================================

SAGE_APP_STYLE = """
QWidget {
    background-color: #1a1a1a;
    color: #c8c8c8;
    font-family: 'Malgun Gothic', serif;
    font-size: 13px;
}

/* 일반 버튼 */
QPushButton {
    background-color: #2e2e2e;
    color: #b8b8b8;
    border: 1.5px solid #484848;
    border-radius: 6px;
    padding: 0px 12px;
    font-size: 12px;
    font-weight: 700;
    min-height: 34px;
}
QPushButton:hover    { background-color: #383838; border-color: #686868; }
QPushButton:pressed  { background-color: #242424; }
QPushButton:disabled { background-color: #222222; color: #505050; border-color: #363636; }

/* 전송 버튼 */
QPushButton#SendButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3c3c3c, stop:1 #2e2e2e);
    color: #e0e0e0;
    border: 1.5px solid #565656;
    border-radius: 8px;
    padding: 0px 20px;
    font-size: 13px;
    font-weight: 800;
    min-height: 42px;
    max-height: 42px;
}
QPushButton#SendButton:hover { background-color: #484848; border-color: #787878; }

/* 마이크 버튼 */
QPushButton#MicButton {
    background-color: #2e2e2e;
    color: #a0a0a0;
    border: 1.5px solid #484848;
    border-radius: 8px;
    min-width: 42px; max-width: 42px;
    min-height: 42px; max-height: 42px;
    padding: 0;
    font-size: 15px;
}
QPushButton#MicButton:hover { background-color: #383838; }

/* 학습 시작 버튼 */
QPushButton#LearnButton {
    background-color: #2e2e2e !important;
    color: #b8b8b8 !important;
    border: 1.5px solid #484848;
    border-radius: 6px;
    padding: 0px 14px;
    font-size: 12px;
    font-weight: 800;
    min-height: 34px;
}
QPushButton#LearnButton:hover    { background-color: #383838; }
QPushButton#LearnButton:disabled { background-color: #222222; color: #505050; }

/* 채팅 출력 영역 */
QTextEdit#ChatOutput {
    background-color: #1e1e1e;
    border: none;
    padding: 14px 16px;
    color: #c0c0c0;
    font-size: 13px;
    selection-background-color: #404040;
}

/* 채팅 입력창 */
QLineEdit#ChatInput {
    background-color: #262626;
    border: 1.5px solid #484848;
    border-radius: 8px;
    padding: 10px 14px;
    color: #d0d0d0;
    font-size: 12px;
    selection-background-color: #404040;
    min-height: 42px;
    max-height: 42px;
}
QLineEdit#ChatInput:focus { border-color: #787878; }

/* 이름 / 나이 입력창 */
QLineEdit#NameInput {
    background-color: #262626;
    border: 1.5px solid #484848;
    border-radius: 6px;
    padding: 4px 10px;
    color: #d0d0d0;
    font-size: 12px;
    min-height: 32px;
    max-height: 32px;
}
QLineEdit#NameInput:focus { border-color: #787878; }

/* 하단 상태 라벨 */
QLabel#StatusLabel {
    color: #909090;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 16px;
    background-color: #161616;
    border-top: 1.5px solid #323232;
}

/* 스크롤바 */
QScrollBar:vertical              { background: #1a1a1a; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical      { background: #484848; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #686868; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical    { height: 0; }
"""

SAGE_PANELS = {
    # ── 패널별 명도 계층 ─────────────────────────────────
    # 왼쪽 패널: #1a1a1a (중간 차콜)
    # 헤더:      #111111 (가장 어두운 강조)
    # 오른쪽:    #1e1e1e (살짝 밝아 구분)
    # 버튼 바:   #222222 (한 단계 더 밝음)
    # 설정 패널: #262626 (입력창 배경과 통일)
    # 입력 영역: #222222 (버튼 바와 동일)
    "left":     "background-color: #1a1a1a; border-right: 1.5px solid #323232;",
    "header":   "background-color: #111111; border: none;",
    "avatar":   "background-color: #1a1a1a;",
    "right":    "background-color: #1e1e1e;",
    "topbar":   "background-color: #222222; border-bottom: 1.5px solid #323232;",
    "setup":    "background-color: #262626; border-bottom: 1.5px solid #323232;",
    "input":    "background-color: #222222; border-top: 1.5px solid #323232;",
    "photo":    "background-color: #2a2a2a; border-radius: 130px;",

    # ── 헤더 텍스트 ─────────────────────────────────────
    "title_color":    "#e0e0e0",
    "subtitle_color": "#686868",
    "soullink_color": "#909090",

    # ── 상태 바 ─────────────────────────────────────────
    "status_text":  "기억 복원 완료 · 연결됨",
    "status_color": "#909090",
    "status_bg":    "#161616",

    # ── 채팅창 ──────────────────────────────────────────
    "chat_placeholder": "그리운 마음을 전해보세요...",
    "chat_open_msg":    "기억의 문이 열렸습니다",

    # ── AI 말풍선 ────────────────────────────────────────
    "msg_ai_bg":     "#2a2a2a",
    "msg_ai_border": "#3e3e3e",
    "msg_ai_color":  "#c0c0c0",
    "msg_ai_name":   "#787878",

    # ── 사용자 말풍선 ────────────────────────────────────
    "msg_user_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3c3c3c,stop:1 #2e2e2e)",
    "msg_user_color": "#e0e0e0",
    "msg_user_name":  "#909090",
}


# ============================================================
# [4] 활성 테마 반환 함수
# ============================================================

def get_theme():
    """
    ACTIVE_THEME 값에 따라 QSS 스타일시트와 패널 색상 딕셔너리를 반환한다.

    반환값:
        (app_style: str, panels: dict)
        - app_style : self.setStyleSheet(app_style) 에 전달하는 QSS 문자열
        - panels    : panels["left"] 형태로 각 위젯의 스타일에 사용하는 딕셔너리
    """
    if ACTIVE_THEME == "sage":
        return SAGE_APP_STYLE, SAGE_PANELS
    return INDIGO_APP_STYLE, INDIGO_PANELS