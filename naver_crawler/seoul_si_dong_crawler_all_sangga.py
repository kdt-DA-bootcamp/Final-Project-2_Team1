import os
import time
import json
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ✅ 토큰 추출 함수
def get_auth_token():
    options = Options()
    options.add_argument("--headless=new")
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
            res = requests.get(url, headers=headers)
            if res.status_code == 403:
                print(f"❌ 403 에러 발생 - [ {gu_name} - {dong_name} ] cortarNo = {cortar_no}")
                return None
            elif res.status_code != 200:
                print(f"❌ 요청 실패: {res.status_code}")
                return None

            data = res.json().get("articleList", [])
            if not data:
                break
            articles.extend(data)
            print(f"📦 {gu_name} - {dong_name} | Page {page} - {len(data)}건 수집됨")
            page += 1
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ 예외 발생: {e}")
            return None

    return articles


# ✅ 전체 수집 실행 함수
def crawl_all_office_articles(token):
    cortar_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\cortarNO\서울시_법정동_cortarNo.csv"
    save_base = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\서울시_상가전체정보"

    cortar_df = pd.read_csv(cortar_path)

    for _, row in cortar_df.iterrows():
        dong = str(row["동이름"]).strip()
        gu = str(row["구이름"]).strip()
        cortar_no = str(row["cortarNo"]).strip()

        if not cortar_no.isdigit() or len(cortar_no) != 10:
            print(f"⚠️ 잘못된 cortarNo: {gu} - {dong} → {cortar_no}")
            continue

        result = fetch_articles_by_dong(gu, dong, cortar_no, token)
        if result is None or len(result) == 0:
            continue

        os.makedirs(os.path.join(save_base, gu), exist_ok=True)
        save_path = os.path.join(save_base, gu, f"{dong}_상가.csv")
        pd.DataFrame(result).to_csv(save_path, index=False, encoding="utf-8-sig")
        print(f"✅ 저장 완료 → {save_path}\n")


# 🚀 실행
if __name__ == "__main__":
    token = get_auth_token()
    if token:
        crawl_all_office_articles(token)
    else:
        print("❌ 토큰 추출 실패")
