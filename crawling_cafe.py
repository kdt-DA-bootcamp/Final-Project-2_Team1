#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울시 자치구별 카페 크롤러 (GraphQL 내부 API)
- 25개 자치구 반복
- "지역명 카페" 키워드 + offset으로 최대 300건 수집
- 429 대응: 백오프 및 재시도
- 중간 중단 시 진행상황 저장(resume 가능)
- 페이지별로 임시 CSV 저장
- 기존 CSV 이어쓰기 (중복 제거)
"""

import requests
import time
import random
import csv
import math
import os
import json
from urllib.parse import quote

# ───────────── 설정 ─────────────
QUERY = "카페"                      # 기본 검색어
ITEMS_PER_PAGE = 32                 # 한 번에 가져올 아이템 수
OUTPUT_FILE = "seoul_cafes.csv"    # 결과 저장 파일
PROGRESS_FILE = "progress.json"    # 진행상황 저장 파일

# GraphQL endpoint
GRAPHQL_URL = "https://p-api.place.naver.com/graphql"

# HTTP headers
COMMON_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/135.0.0.0 Safari/537.36",
    "Accept":          "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type":    "application/json",
    "Origin":          "https://search.naver.com",
    "Referer":         f"https://search.naver.com/search.naver?query={quote(QUERY)}",
}

# 서울시 25개 자치구 리스트
REGIONS = [
    "종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구",
    "강북구","도봉구","노원구","은평구","서대문구","마포구","양천구","강서구",
    "구로구","금천구","영등포구","동작구","관악구","서초구","강남구","송파구","강동구"
]

# GraphQL 쿼리 본문
GRAPHQL_QUERY = """
query getRestaurants($restaurantListInput: RestaurantListInput) {
  restaurantList(input: $restaurantListInput) {
    total
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
        f"https://search.naver.com/search.naver?query={quote(QUERY)}",
        headers={
            "User-Agent": COMMON_HEADERS["User-Agent"],
            "Accept-Language": COMMON_HEADERS["Accept-Language"]
        }
    )
    return session


def load_existing():
    """기존 CSV 로드 (이어서 저장용)"""
    if not os.path.isfile(OUTPUT_FILE):
        return []
    rows = []
    with open(OUTPUT_FILE, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    print(f"기존에 {len(rows)}개 레코드 로드됨.")
    return rows


def fetch_region(session, region, offset):
    """GraphQL API 요청(region 키워드 + offset) + 백오프"""
    query_text = f"{region} {QUERY}"
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {"restaurantListInput": {
            "query": query_text,
            "x": "127.00698",
            "y": "37.613339",
            "start": offset,
            "display": ITEMS_PER_PAGE,
            "isNx": True
        }}
    }
    for attempt in range(5):
        resp = session.post(GRAPHQL_URL, headers=COMMON_HEADERS, json=payload)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = (attempt + 1) * 2 + random.random()
            print(f"[429] {wait:.1f}s 후 재시도 ({attempt+1}/5)")
            time.sleep(wait)
            continue
        print(f"[{resp.status_code}] {resp.reason}")
        try:
            print("Error JSON:", resp.json())
        except:
            print("Error Text:", resp.text[:200])
        return None
    raise RuntimeError("5회 재시도 실패")


def parse_places(data, region):
    """응답 JSON에서 지역, 이름, 평점, 리뷰 수 추출"""
    items = data.get("data", {})
    items = items.get("restaurantList", {})
    items = items.get("items") or []
    return [
        {"region": region,
         "name": it.get("name"),
         "score": it.get("visitorReviewScore"),
         "reviewCount": it.get("totalReviewCount")} for it in items
    ]


def load_progress():
    """진행상황 로드"""
    if os.path.isfile(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE, encoding='utf-8'))
    return {"region_index": 0, "page": 0}


def save_progress(region_index, page):
    """진행상황 저장"""
    json.dump({"region_index": region_index, "page": page},
              open(PROGRESS_FILE, 'w', encoding='utf-8'))


def save_csv(rows):
    """중복 제거 후 CSV 저장"""
    if not rows:
        return
    seen = set(); unique = []
    for r in rows:
        key = (r['region'], r['name'])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(unique[0].keys()))
        writer.writeheader()
        writer.writerows(unique)
    print(f"저장: {OUTPUT_FILE} ({len(unique)}개)")


def main():
    session = init_session()
    all_rows = load_existing()
    prog = load_progress()

    for idx, region in enumerate(REGIONS):
        if idx < prog['region_index']:
            continue
        print(f"▶ {region} 수집 시작...({idx})")
        start_page = prog['page'] if idx == prog['region_index'] else 0

        # 첫 페이지 처리 및 총 페이지 수 계산
        first_offset = start_page * ITEMS_PER_PAGE
        try:
            first_data = fetch_region(session, region, first_offset)
        except RuntimeError:
            print(f"  {region} page {start_page+1} 실패, 스킵")
            save_progress(idx+1, 0)
            continue
        if not first_data or not first_data.get('data'):
            print(f"  {region} page {start_page+1} 데이터 없음, 스킵")
            save_progress(idx+1, 0)
            continue
        total = first_data['data']['restaurantList'].get('total')
        if total is None:
            print(f"  {region} total 값 없음, 스킵")
            save_progress(idx+1, 0)
            continue
        pages = math.ceil(total / ITEMS_PER_PAGE)
        print(f"총 {total}건 → {pages}페이지")

        # 첫 페이지 저장
        all_rows.extend(parse_places(first_data, region))
        save_progress(idx, start_page)
        save_csv(all_rows)
        time.sleep(random.uniform(0.5, 1.5))

        # 나머지 페이지
        for page in range(start_page+1, pages):
            offset = page * ITEMS_PER_PAGE
            print(f"  {region} page {page+1}/{pages} offset={offset}")
            try:
                data = fetch_region(session, region, offset)
            except RuntimeError:
                print(f"  {region} page {page+1} 실패, 중단")
                break
            if not data or not data.get('data'):
                print(f"  {region} page {page+1} 데이터 없음, 중단")
                break
            all_rows.extend(parse_places(data, region))
            save_progress(idx, page)
            save_csv(all_rows)
            time.sleep(random.uniform(0.5, 1.5))

        # 다음 지역으로 이동
        save_progress(idx+1, 0)

    # 완료 후 프로그레스 파일 삭제
    if os.path.isfile(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == '__main__':
    main()