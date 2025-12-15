Memorial-chatbot-Project/
├── config/
│   └── .env                   # [보안] API 키 및 환경 변수 저장
├── data/
│   └── sample.txt             # [원천 데이터] 카카오톡 내보내기 파일 
├── src/
│   ├── core/
│   │   ├── gpt_core.py        # GPT API 통신 및 페르소나 적용
│   │   ├── voice_util.py      # 음성 녹음 및 정규화
│   │   └── persona_process/   # 페르소나 구축 3단계 로직 모음
│   │       ├── kakao_cleaner.py     # 메시지 추출 및 정제
│   │       ├── style_extractor.py   # 말투 및 성격 분석 (GPT 호출)
│   │       └── persona_builder.py   # 프롬프트 최종 포맷팅
│   └── app_gui.py             # PyQt6 GUI 및 스레드 통합 관리
├── run.py                     # 애플리케이션 시작점
└── requirements.txt           # 필수 파이썬 패키지 목
