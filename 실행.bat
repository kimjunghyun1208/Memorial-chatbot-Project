@echo off
title AI 추모 챗봇 실행기
cd /d "%~dp0"

echo [1/2] 필수 라이브러리 설치 확인 중...
pip install -r requirements.txt

echo [2/2] 프로그램 실행 중...
python run.py

pause