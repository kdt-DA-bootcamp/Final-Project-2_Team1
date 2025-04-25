#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV에 있는 카페명 리스트를 순회하며 내부 GraphQL API로 가격대·편의옵션·주차 여부를 크롤링
- /mnt/data/카페_상권_매핑_데이터.csv 의 '상호명' 컬럼 로드 (다양한 인코딩 시도)
- GraphQL 호출로 priceCategory, options, parking 정보만 조회
- 결과를 cafe_search_results.csv에 저장 (이어쓰기 + 중복 제거)
- .env 파일에서 NAVER_CLIENT_ID/SECRET 로드
- 429 응답 시 백오프 최대 5회 재시도
- 진행상황을 progress_combined.json에 저장하여 재실행 시 이어서 수행
"""
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import requests
import time
import random
import csv
import json

# 환경 변수
CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError('NAVER_CLIENT_ID 및 NAVER_CLIENT_SECRET 환경변수를 설정하세요.')

# 파일 및 API 설정
INPUT_FILE = '카페_상권_매핑_데이터.csv'
OUTPUT_FILE = 'cafe_search_results.csv'
PROGRESS_FILE = 'progress_combined.json'
ITEMS_PER_PAGE = 1

# 내부 GraphQL API (가격대·편의옵션 조회)
GRAPHQL_URL = 'https://p-api.place.naver.com/graphql'
GRAPHQL_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/135.0.0.0 Safari/537.36'),
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'Referer': 'https://search.naver.com/search.naver?query='
}
GRAPHQL_QUERY = '''
query getRestaurants($input: RestaurantListInput) {
  restaurantList(input: $input) {
    items {
      priceCategory
      options
    }
  }
}
'''

# 유틸 함수

def load_cafe_list():
    encodings = ['cp949', 'utf-8-sig', 'latin1']
    for enc in encodings:
        try:
            df = pd.read_csv(INPUT_FILE, encoding=enc)
            if '상호명' in df.columns:
                return df['상호명'].dropna().unique().tolist()
        except:
            continue
    raise ValueError("상호명 컬럼을 가진 CSV를 읽을 수 없습니다.")


def load_progress():
    if os.path.isfile(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE, encoding='utf-8'))
    return {'index': 0}


def save_progress(idx):
    json.dump({'index': idx}, open(PROGRESS_FILE, 'w', encoding='utf-8'))


def fetch_graphql(session, name):
    payload = {
        'query': GRAPHQL_QUERY,
        'variables': {
            'input': {
                'query': f'{name} 서울 카페',
                'x': '127.00698',
                'y': '37.613339',
                'start': 0,
                'display': ITEMS_PER_PAGE,
                'isNx': True
            }
        }
    }
    for attempt in range(5):
        resp = session.post(GRAPHQL_URL, headers=GRAPHQL_HEADERS, json=payload)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            items = data.get('restaurantList', {}).get('items') or []
            return items[0] if items else {}
        if resp.status_code == 429:
            time.sleep((attempt + 1) * 2 + random.random())
            continue
        break
    return {}


def save_results(rows):
    if not rows:
        return
    seen = set()
    unique = []
    for r in rows:
        if r['query'] not in seen:
            seen.add(r['query'])
            unique.append(r)
    fieldnames = ['query', 'priceCategory', 'options', 'parking']
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in unique:
            writer.writerow({
                'query': r['query'],
                'priceCategory': r.get('priceCategory', ''),
                'options': r.get('options', ''),
                'parking': r.get('parking', '')
            })
    print(f'저장: {OUTPUT_FILE} ({len(unique)}개)')


def main():
    session = requests.Session()
    cafe_list = load_cafe_list()
    prog = load_progress()
    all_rows = []
    if os.path.isfile(OUTPUT_FILE):
        with open(OUTPUT_FILE, newline='', encoding='utf-8-sig') as f:
            for record in csv.DictReader(f):
                all_rows.append(record)

    for idx in range(prog['index'], len(cafe_list)):
        name = cafe_list[idx]
        print(f'▶ 처리 중: {idx+1}/{len(cafe_list)} - {name}')
        gf = fetch_graphql(session, name)
        price = gf.get('priceCategory', '')
        opts_raw = gf.get('options') or ''
        # 쉼표 구분자로 분할하여 실제 옵션 리스트 구성
        opts_list = [opt.strip() for opt in opts_raw.split(',') if opt.strip()]
        # 옵션 텍스트 공백 제거
        opts_str = ''.join(opts_list)
        parking = 'Yes' if any('주차' in opt for opt in opts_list) else 'No'
        all_rows.append({
            'query': name,
            'priceCategory': price,
            'options': opts_str,
            'parking': parking
        })
        save_progress(idx + 1)
        save_results(all_rows)
        time.sleep(random.uniform(0.5, 1.5))

    if os.path.isfile(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == '__main__':
    main()