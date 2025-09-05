#!/bin/bash
set -o errexit

# Build Command에서 테이블 생성을 처리하도록 변경하고,
# Start Command는 오직 웹 서버를 실행하는 역할만 하도록 분리합니다.
# 이 파일은 이제 사용되지 않을 수 있지만, 만약을 위해 gunicorn 실행 명령어만 남겨둡니다.
gunicorn --worker-class eventlet -w 1 app:app