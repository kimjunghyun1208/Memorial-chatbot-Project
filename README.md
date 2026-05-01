# 🤖 AI 추모 챗봇 (Memorial Chatbot Project)

고인의 카카오톡 대화 데이터와 음성을 학습하여, 얼굴 영상과 목소리로 대화할 수 있는 AI 추모 챗봇입니다.

---

## 🌟 주요 기능

| 기능 | 설명 |
|------|------|
| 🧠 **페르소나 생성** | 카카오톡 대화 데이터로 말투·성격 자동 분석 |
| 💬 **AI 대화** | GPT 기반 자연어 대화 (텍스트 + 음성 입력) |
| 🎤 **음성 클론** | ElevenLabs로 고인의 목소리 재현 |
| 🎬 **아바타 영상** | D-ID로 고인의 얼굴이 말하는 영상 생성 |
| 📷 **정면 얼굴 합성** | 여러 각도 사진 → fal.ai Nano Banana 2로 정면 사진 생성 |

---

## 📂 프로젝트 구조

```
Memorial-chatbot-Project/
├── config/
│   └── .env                  # API 키 설정 (직접 생성 필요)
├── data/
│   └── sample.txt            # 카카오톡 대화 파일 (직접 추가 필요)
├── src/
│   ├── app_gui.py            # 메인 GUI
│   ├── data/
│   │   └── persona/
│   │       └── photo.jpg     # 고인 사진 (직접 추가 필요)
│   └── core/
│       ├── gpt_core.py       # GPT 대화 엔진
│       ├── voice_util.py     # ElevenLabs 음성 처리
│       ├── did_client.py     # D-ID 영상 생성
│       ├── face_synthesizer.py  # 얼굴 합성 (fal.ai)
│       └── persona_process/
│           ├── kakao_cleaner.py
│           ├── style_extractor.py
│           ├── persona_builder.py
│           ├── memory_extractor.py
│           ├── memory_prompt_builder.py
│           └── memory_store.py
├── requirements.txt
└── run.py
```

---

## 🚀 설치 및 실행 방법

### 1. 클론
```bash
git clone https://github.com/YourUsername/Memorial-chatbot-Project.git
cd Memorial-chatbot-Project
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. ffmpeg 설치 (Windows)
```bash
winget install ffmpeg
```

### 4. `config/.env` 파일 생성
프로젝트 루트의 `config/` 폴더 안에 `.env` 파일을 직접 만들고 아래 내용을 입력하세요:
```
OPENAI_API_KEY=sk-...
XI_API_KEY=...
VOICE_ID=...
DID_API_KEY=...
FAL_KEY=key_...
```

| 키 | 발급처 |
|----|--------|
| OPENAI_API_KEY | https://platform.openai.com |
| XI_API_KEY | https://elevenlabs.io |
| VOICE_ID | ElevenLabs 음성 클론 후 발급 |
| DID_API_KEY | https://www.d-id.com |
| FAL_KEY | https://fal.ai |

### 5. 필수 파일 준비
- `data/sample.txt` → 카카오톡 대화 내보내기 파일
- `src/data/persona/photo.jpg` → 고인 사진 (정면 사진 권장)

### 6. 실행
```bash
python run.py
```
또는
```bash
cd src
python app_gui.py
```

---

## 💡 사용 방법

1. **목소리 추출**: `🎬 목소리 추출용 영상` 버튼으로 고인의 영상에서 음성 추출
2. **정면 사진 합성**: `📷 사진 다중 선택`으로 여러 각도 사진 선택 후 `🔮 정면 합성 시작` 클릭
3. **대화 시작**: 텍스트 입력 또는 `🎤` 버튼으로 음성 대화

---

## 👥 팀원

| 이름 | 담당 |
|------|------|
| 김정현 | GUI 및 스레드 통합, D-ID 영상 연동, 얼굴 합성 |
| 윤준하 | 페르소나 구축 (카카오톡 분석, GPT 프롬프트) |
| 노일국 | UI & 프론트엔드 |
| 김준서 | 음성 입출력 (ElevenLabs, STT) |

---

## ⚠️ 주의사항

- `config/.env` 파일은 절대 깃허브에 올리지 마세요 (API 키 유출 위험)
- 고인의 사진·음성 데이터는 개인정보이므로 깃허브에 올리지 마세요
- fal.ai API는 이미지 생성 시 비용이 발생합니다 (약 $0.08/장)