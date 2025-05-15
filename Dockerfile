# 1. 환경설정
FROM python:3.9-slim

# 2. 경로 및 OS 소프트웨어 설치
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    libpq-dev gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# RUN apt install libmariadb3 libmariadb-dev

# 3. 필요 라이브러리 설치
# 캐싱 ---- 
COPY 최종프로젝트_서울카페분석_배포용/requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
# 캐싱 ----

# 4. 소스코드 복사
COPY 최종프로젝트_서울카페분석_배포용 .

# 5. 실행
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "통합시스템.py", "--server.port=8501", "--server.address=0.0.0.0"]