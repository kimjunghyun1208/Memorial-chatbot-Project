# 🤖 Memorial-chatbot-Project (AI 추모 챗봇)

## 🌟 프로젝트 개요

본 프로젝트는 특정 인물의 카카오톡 대화 데이터를 분석하여 그 사람의 말투와 성격을 재현하는 인공지능 챗봇 시스템입니다. PyQt6 기반의 다크 모드 GUI를 통해 **텍스트 및 음성으로 대화**하며 감정적 교류를 시뮬레이션하는 통합 프레임워크입니다.

## 🚀 MVP 목표

* **페르소나 생성:** 카카오톡 메시지 파일을 입력받아 GPT를 통해 말투 및 성격 분석 후, 시스템 프롬프트를 자동 생성합니다.
* **비동기 대화:** PyQt6 GUI에서 사용자와 챗봇이 자연스러운 속도로 텍스트 기반 대화를 주고받을 수 있도록 구현합니다.
* **음성 입력 기반 마련:** 사용자의 음성을 녹음하고 정규화하여 STT(Speech-to-Text) API로 전송할 수 있는 워크플로우를 완성합니다.

## 👥 팀원 및 역할 분담

| 이름 | 담당 영역 | 주요 개발 항목 |
| :--- | :--- | :--- |
| **김정현** | **GUI 및 스레드 통합** | PyQt6 UI 개발 (다크 모드), GPTWorker/RecorderWorker 스레드 관리, 타이핑 효과 구현. |
| **윤준하** | **페르소나 구축** | kakao_cleaner.py, style_extractor.py, persona_builder.py 모듈 개발, GPT API 호출 로직. |
| **노일국** | **UI & 프론트엔드** | kakao_cleaner.py, style_extractor.py, persona_builder.py 모듈 개발, GPT API 호출 로직. |
| **김준서** | **음성 입/출력** | sounddevice/soundfile을 사용한 녹음 및 정규화 (voice_util.py), STT/TTS 모듈 통합 (추가 개발 필요). |


## 📂 프로젝트 구조 및 모듈 설명

프로젝트는 기능별로 명확하게 분리되어 있습니다. 특히 핵심 로직은 `src/core` 폴더 아래에 모여있습니다.


| 폴더/파일 | 역할 | 포함된 주요 기능 |
| :--- | :--- | :--- |
| **`run.py`** | **실행 진입점** | `app_gui.py`를 호출하여 애플리케이션을 시작합니다. |
| **`config/.env`** | **환경 변수** | OpenAI API Key 등 민감한 정보를 저장합니다. (필수: `.gitignore` 적용) |
| **`data/`** | **원본 데이터** | [cite_start]분석 대상인 카카오톡 대화 내보내기 파일 (`sample.txt` [cite: 43-49])이 위치합니다. |
| **`src/app_gui.py`** | **전체 GUI** | `AIChatBotGUI` 클래스, UI 구성, 스레드(Worker) 시그널 연결. |
| **`src/core/gpt_core.py`** | **API 통신 엔진** | `chat_with_persona` 함수 정의, 대화 문맥 관리, 프롬프트 적용. |
| **`src/core/voice_util.py`** | **음성 처리** | `record` 및 `normalize_wav` 함수를 포함한 모든 오디오 처리 로직. |
| **`src/core/persona_process/`** | **페르소나 3단계** | 카카오톡 데이터 정제, GPT 분석, 프롬프트 포맷팅 모듈을 분리하여 저장. |



## 🚀 로컬 실행 방법

1.  **클론 및 가상 환경 설정:**
    ```bash
    git clone [https://github.com/YourUsername/Memorial-chatbot-Project.git](https://github.com/YourUsername/Memorial-chatbot-Project.git)
    cd Memorial-chatbot-Project
    python -m venv .venv
    # (가상 환경 활성화)
    ```

2.  **패키지 설치:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **환경 변수 설정:**
    * `config/.env` 파일을 생성하고 OpenAI API 키를 입력합니다.

4.  **애플리케이션 실행:**
    ```bash
    python run.py
    ```

## ⚠️ 팀원 협업 유의사항

* **GitHub 보안:** 절대로 `config/.env`, `*.wav` (녹음 파일), `*.pyc` 파일을 커밋하지 않도록 `.gitignore` 파일을 철저히 관리하십시오.
* **GUI 스레드:** GUI 관련 코드는 오직 `app_gui.py`의 메인 스레드에서만 수정해야 합니다. 백그라운드 작업은 반드시 `QThread` 기반의 Worker (예: `GPTWorker`)를 사용하십시오.
* **경로:** 파일 입출력 시, 로컬 환경에 따라 경로 문제가 생기지 않도록 `os.path.join`을 사용하여 경로를 구성하십시오.

## 기존 파일 이름,새 경로,변경 사항
* **기존경로 ➡️ 새 경로 / 변경사항**
* **main.py,src** ➡️ **app_gui.py,GUI** / 실행 및 페르소나 생성 로직을 통합하는 메인 파일이 됩니다. GPT API 호출 함수는 **gpt_core.py**로 이동합니다.
* **D.txt,src** ➡️ **core / voice_util.py** / 음성 녹음 및 정규화 로직이 들어갑니다.
* **C.txt,src ➡️ app_gui.py /** PyQt6 GUI 클래스(AIChatBotGUI)와 스레드 클래스(DLWorker → GPTWorker)가 들어갑니다.
* **kakao_cleaner.py ➡️ src / core / persona_process / kakao_cleaner.py /** 파일 경로 정의를 수정해야 합니다.
* **style_extractor.py ➡️ src / core / persona_process / style_extractor.py /** 환경 변수 로드 경로를 수정해야 합니다.
* **persona_builder.py ➡️ src / core / persona_process / persona_builder.py /** 변경 사항 없이 그대로 사용 가능합니다.
* **sample.txt,data ➡️ sample.txt /** 카카오톡 데이터 원본 파일입니다.
