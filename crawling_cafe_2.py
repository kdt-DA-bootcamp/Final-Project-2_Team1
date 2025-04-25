#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV에 있는 카페명 리스트를 순회하며 네이버 GraphQL API로 검색
- /mnt/data/카페_상권_매핑_데이터.csv 의 '상호명' 컬럼을 로드 (다양한 인코딩 시도)
- 각 카페명으로 검색 후, 첫 결과의 평점·리뷰 수 추출
- 결과를 cafe_search_results.csv에 저장 (기존 파일 이어쓰기)
- 429 응답 시 백오프 및 최대 5회 재시도
- 진행상황을 progress_cafe_search.json에 기록해 재실행 시 이어서 수행
"""

import pandas as pd
import requests
import time
import random
import csv
import os
import json
from urllib.parse import quote

# 설정
INPUT_FILE = "카페_상권_매핑_데이터.csv"
OUTPUT_FILE = "cafe_search_results.csv"
PROGRESS_FILE = "progress_cafe_search.json"
ITEMS_PER_PAGE = 1

# GraphQL 엔드포인트 및 헤더
GRAPHQL_URL = "https://p-api.place.naver.com/graphql"
COMMON_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/135.0.0.0 Safari/537.36",
    "Accept":          "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type":    "application/json",
    "Origin":          "https://search.naver.com",
    "Referer":         "https://search.naver.com/search.naver?query="
}

# GraphQL 쿼리
GRAPHQL_QUERY = """
query getRestaurants($restaurantListInput: RestaurantListInput) {
  restaurantList(input: $restaurantListInput) {
    items {
      name
      visitorReviewScore
      totalReviewCount
    }
  }
}
"""

# ─────────── 유틸 함수 ────────────

def init_session():
    """세션 생성 및 초기 페이지 방문"""
    session = requests.Session()
    session.get(
        "https://search.naver.com/search.naver?query=카페",
        headers={
            "User-Agent": COMMON_HEADERS["User-Agent"],
            "Accept-Language": COMMON_HEADERS["Accept-Language"]
        }
    )
    return session


def load_cafe_list():
    """CSV에서 상호명(카페명) 컬럼 로드 (다양한 인코딩 시도)"""
    encodings = ['cp949', 'utf-8-sig', 'latin1']
    last_err = None
    for enc in encodings:
        try:
            df = pd.read_csv(INPUT_FILE, encoding=enc)
        except Exception as e:
            last_err = e
            continue
        if '상호명' not in df.columns:
            raise ValueError(f"'상호명' 컬럼이 없습니다. ({enc}로 읽기 시)")
        return df['상호명'].dropna().unique().tolist()
    raise UnicodeDecodeError(f"읽기 실패: {last_err}")


def load_progress():
    """진행상황 로드"""
    if os.path.isfile(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE, encoding='utf-8'))
    return {'index': 0}


def save_progress(idx):
    """진행상황 저장"""
    json.dump({'index': idx}, open(PROGRESS_FILE, 'w', encoding='utf-8'))


def fetch_cafe(session, cafe_name):
    """카페명으로 GraphQL 요청 후 JSON 반환"""
    payload = {
        'query': GRAPHQL_QUERY,
        'variables': {
            'restaurantListInput': {
                'query': cafe_name,
                'x': '127.00698',
                'y': '37.613339',
                'start': 0,
                'display': ITEMS_PER_PAGE,
                'isNx': True
            }
        }
    }
    for attempt in range(5):
        resp = session.post(GRAPHQL_URL, headers=COMMON_HEADERS, json=payload)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = (attempt+1)*2 + random.random()
            print(f"[429] {wait:.1f}s 후 재시도 ({attempt+1}/5)")
            time.sleep(wait)
            continue
        return None
    return None


def save_results(rows):
    """중복 제거 후 CSV 저장"""
    if not rows:
        return
    seen = set()
    unique = []
    for r in rows:
        key = r['query']
        if key not in seen:
            seen.add(key)
            unique.append(r)
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(unique[0].keys()))
        writer.writeheader()
        writer.writerows(unique)
    print(f"결과 저장: {OUTPUT_FILE} ({len(unique)}개)")


def main():
    session = init_session()
    cafe_list = load_cafe_list()
    prog = load_progress()
    all_rows = []

    # 기존 결과 로드
    if os.path.isfile(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    all_rows.append(r)
        except Exception:
            pass

    for idx in range(prog['index'], len(cafe_list)):
        name = cafe_list[idx]
        print(f"▶ 검색: {name} ({idx+1}/{len(cafe_list)})")
        data = fetch_cafe(session, name)
        found_name = ''
        score = ''
        reviewCount = ''
        if data and data.get('data'):
            items = data['data']['restaurantList']['items']
            if items:
                it = items[0]
                found_name = it.get('name', '')
                score = it.get('visitorReviewScore', '')
                reviewCount = it.get('totalReviewCount', '')
        all_rows.append({
            'query': name,
            'found_name': found_name,
            'score': score,
            'reviewCount': reviewCount
        })
        save_progress(idx+1)
        save_results(all_rows)
        time.sleep(random.uniform(0.5, 1.5))

    if os.path.isfile(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == '__main__':
    main()