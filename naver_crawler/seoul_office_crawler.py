import os
import time
import json
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ✅ 토큰 추출 함수
def get_auth_token():
    print("\n🔑 [DEBUG] 토큰 추출 시도 중...")
    options = Options()
    options.add_argument("--headless=new")  # ✅ headless 다시 활성화
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=options)
    driver.get("https://new.land.naver.com/offices?ms=37.5375,127.0061,16&a=SG&e=RETAIL")
    time.sleep(3)

    logs = driver.get_log("performance")
    token = None
    for entry in logs:
        try:
            message = json.loads(entry["message"])["message"]
            if message["method"] == "Network.requestWillBeSent":
                headers = message.get("params", {}).get("request", {}).get("headers", {})
                if "authorization" in headers:
                    token = headers["authorization"]
                    print(f"🔐 토큰 추출 완료: {token[:30]}...")
                    break
        except Exception:
            continue
    driver.quit()
    return token

# ✅ 개별 동 매물 수집 함수
def fetch_articles_by_dong(gu_name, dong_name, cortar_no, token):
    headers = {
        "Authorization": token,
        "Referer": f"https://new.land.naver.com/offices?cortarNo={cortar_no}",
        "User-Agent": "Mozilla/5.0"
    }

    articles = []
    page = 1

    while True:
        url = (
            f"https://new.land.naver.com/api/articles?"
            f"cortarNo={cortar_no}&order=rank&realEstateType=SG"
            f"&tradeType=&priceType=RETAIL&page={page}"
        )
        try:
            res = requests.get(url, headers=headers, timeout=5)
            print(f"🌐 요청 URL (Page {page}): {url}")
            if res.status_code == 403:
                print(f"❌ 403 에러 발생 - [ {gu_name} - {dong_name} ] cortarNo = {cortar_no}")
                return None
            elif res.status_code != 200:
                print(f"❌ 요청 실패: {res.status_code}")
                return None

            data = res.json().get("articleList", [])
            if not data:
                print(f"📭 데이터 없음 - 종료 (Page {page})")
                break
            articles.extend(data)
            print(f"📦 {gu_name} - {dong_name} | Page {page} - {len(data)}건 수집됨")
            page += 1
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ 예외 발생: {e}")
            return None

    return articles

# ✅ 순차 실행 함수
def crawl_seoul_all_dongs_sequential(token):
    cortar_path = r"C:\\Users\\hunae\\Desktop\\bootcamp\\TIL\\최종프로젝트2차\\네이버 매물\\공공데이터 법정동코드\\법정동_동코드_구이름포함.xlsx"
    save_base = r"C:\\Users\\hunae\\Desktop\\bootcamp\\TIL\\최종프로젝트2차\\dong_results\\서울시_상가_전체구"

    cortar_df = pd.read_excel(cortar_path)
    print(f"📄 엑셀 로드 완료! 총 {len(cortar_df)}개 행")
    print("📌 컬럼명:", cortar_df.columns.tolist())

    for _, row in cortar_df.iterrows():
        dong = str(row["동이름"]).strip()
        gu = str(row["구이름"]).strip()
        cortar_no = str(row["cortarNo"]).strip()

        if not cortar_no.isdigit() or len(cortar_no) != 10:
            print(f"⚠️ 잘못된 cortarNo: {gu} - {dong} → {cortar_no}")
            continue

        print(f"\n=== 🚀 시작: [ {gu} - {dong} ] / cortarNo: {cortar_no} ===")
        result = fetch_articles_by_dong(gu, dong, cortar_no, token)

        gu_dir = os.path.join(save_base, gu)
        os.makedirs(gu_dir, exist_ok=True)
        save_path = os.path.join(gu_dir, f"{dong}_상가.csv")

        if result is None or len(result) == 0:
            print(f"⚠️ 매물 없음 또는 수집 실패 → {dong}")
            pd.DataFrame().to_csv(save_path, index=False, encoding="utf-8-sig")
        else:
            pd.DataFrame(result).to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"✅ 저장 완료 → {save_path}")

# ✅ 실행 시작
if __name__ == "__main__":
    print("\n🔄 스크립트 실행 시작")
    token = get_auth_token()
    if token:
        crawl_seoul_all_dongs_sequential(token)
    else:
        print("❌ 토큰 추출 실패")
