
import os
import json
import requests
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

HEADERS = {
    'User-Agent': 'Mozilla 5.0',
    'X-ApiSecret': 'fe5183cc3dea12bd0ce299cf110a75a2',
    'X-ApiKey': 'iphoneap'
}

def generate_seoul_grid(lat_start=37.4133, lat_end=37.7151, lng_start=126.7341, lng_end=127.2693, step=0.01):
    grid = []
    lat = lat_start
    while lat <= lat_end:
        lng = lng_start
        while lng <= lng_end:
            grid.append((round(lat, 6), round(lng, 6)))
            lng += step
        lat += step
    return grid

# ✅ 페이지 순회 및 전체 컬럼 포함
def fetch_and_parse_store(lat_lng):
    lat, lng = lat_lng
    category = "%EC%B9%B4%ED%8E%98%EB%94%94%EC%A0%80%ED%8A%B8"
    stores = []
    page = 0

    while True:
        url = (
            f"https://www.yogiyo.co.kr/api/v2/restaurants?"
            f"category={category}&items=60&lat={lat}&lng={lng}"
            f"&order=rank&page={page}&search=&serving_type=vd"
        )
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                break
            data = response.json().get("restaurants", [])
            if not data:
                break
            for s in data:
                store = s.copy()
                store["lat"] = lat
                store["lng"] = lng
                stores.append(store)
            page += 1
        except Exception as e:
            print(f"❌ 실패: {lat}, {lng}, page {page} → {e}")
            break

    return lat, lng, stores

def collect_all_stores_by_location():
    coords = generate_seoul_grid()
    pool = Pool(processes=min(cpu_count(), 8))
    results = pool.map(fetch_and_parse_store, coords)
    pool.close()
    pool.join()

    output_dir = "카페디저트_좌표별데이터_전체컬럼(0.01버전)"
    os.makedirs(output_dir, exist_ok=True)

    for lat, lng, stores in results:
        if stores:
            df = pd.DataFrame(stores)
            filename = os.path.join(output_dir, f"{lat}_{lng}.csv")
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"✅ 저장 완료: {filename}")

if __name__ == "__main__":
    collect_all_stores_by_location()
