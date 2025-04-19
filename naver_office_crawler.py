import time
import re
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(service=Service(), options=options)
driver.get("https://new.land.naver.com/offices?ms=37.5385147,127.0050758,16&a=SG:SMS:GM:TJ:APTHGJ:GJCG&e=RETAIL")
time.sleep(2)

try:
    checkbox = driver.find_element(By.ID, "address_group2")
    if checkbox.is_selected():
        label = driver.find_element(By.CSS_SELECTOR, "label[for='address_group2']")
        label.click()
        time.sleep(1)
except Exception as e:
    print("⚠️ 동일매물 묶기 해제 실패:", e)

def get_text(selector, attr=None):
    try:
        el = driver.find_element(By.CSS_SELECTOR, selector)
        return el.get_attribute(attr) if attr else el.text.strip()
    except:
        return ""

def extract_value_from_table(keyword):
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.info_table_item")
        for row in rows:
            ths = row.find_elements(By.TAG_NAME, "th")
            tds = row.find_elements(By.TAG_NAME, "td")
            for i, th in enumerate(ths):
                if keyword in th.text:
                    return tds[i].text.strip()
    except:
        return ""
    return ""

try:
    first_item = driver.find_element(By.CSS_SELECTOR, "div.item_inner")
    link = first_item.find_element(By.CSS_SELECTOR, "a.item_link")
    driver.execute_script("arguments[0].scrollIntoView(true);", link)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(link))
    link.click()
    time.sleep(4)
except Exception as e:
    print("❌ 첫 매물 클릭 실패:", e)

def extract_article_no():
    try:
        return driver.current_url.split("articleNo=")[-1]
    except:
        return ""

article_no = extract_article_no()
latitude = longitude = ""

logs = driver.get_log("performance")
for entry in logs:
    try:
        msg = json.loads(entry["message"])["message"]
        if msg.get("method") != "Network.responseReceived":
            continue
        url = msg.get("params", {}).get("response", {}).get("url", "")
        if f"/api/articles/{article_no}" in url:
            request_id = msg["params"]["requestId"]
            try:
                response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                body = response.get("body", "")
                data = json.loads(body)
                addition = data.get("articleAddition", {})
                latitude = addition.get("latitude", "")
                longitude = addition.get("longitude", "")
                break
            except:
                pass
    except:
        continue

# 👇 여기부터는 기존 그대로 유지 + 일부 순서/요약태그만 수정
매물종류 = get_text("strong.type")
제목 = get_text("span.text")
현장확인일 = get_text("span.label--confirm em.data")
요약태그 = ", ".join([el.text.strip() for el in first_item.find_elements(By.CSS_SELECTOR, "div.tag_area span.tag")])
가격_raw = get_text("div.info_article_price span.price")
보증금, 월세 = 가격_raw.split("/") if "/" in 가격_raw else (가격_raw, "")
계약전용면적 = extract_value_from_table("계약/전용면적")
층수_raw = extract_value_from_table("해당층/총층")
해당층, 총층 = 층수_raw.split("/") if "/" in 층수_raw else (층수_raw, "")
소재지 = extract_value_from_table("소재지")
매물특징 = extract_value_from_table("매물특징")
입주가능일 = extract_value_from_table("입주가능일")
월관리비 = extract_value_from_table("월관리비")
방향 = extract_value_from_table("방향")
현재업종 = extract_value_from_table("현재업종")
추천업종 = extract_value_from_table("추천업종")
주차가능여부 = extract_value_from_table("주차가능여부")
총주차대수 = extract_value_from_table("총주차대수")
난방 = extract_value_from_table("난방(방식/연료)")
용도지역 = extract_value_from_table("용도지역")
건축물용도 = extract_value_from_table("건축물 용도")
주구조 = extract_value_from_table("주구조")
사용승인일 = extract_value_from_table("사용승인일")
매물설명 = get_text("tr.info_table_item pre")
중개사 = get_text("div.table_td_agent strong.info_title")
중개보수금액 = get_text("strong.point5")
중개보수요율 = get_text("em.quadrant_value")
중개보수 = f"{중개보수금액} / {중개보수요율}" if 중개보수금액 else ""
style_attr = get_text("button.main_photo_item", attr="style")
img_url_match = re.search(r'url\("(.*?)"\)', style_attr)
매물사진url = img_url_match.group(1) if img_url_match else ""
중개사정보 = get_text("div.info_agent_wrap")
매물링크 = f"https://new.land.naver.com/offices?articleNo={article_no}"

# ✅ 컬럼 순서 수정 (건축물용도 → 매물번호 순으로)
columns = [
    "제목", "매물종류", "현장확인일", "요약태그", "보증금", "월세", "계약전용면적", "소재지", "매물특징",
    "해당층", "총층", "입주가능일", "월관리비", "방향", "현재업종", "추천업종", "주차가능여부", "총주차대수", "난방",
    "용도지역", "건축물용도", "매물번호", "사용승인일", "매물설명", "중개사", "중개사정보", "중개보수",
    "매물사진url", "위도", "경도", "매물링크"
]

results = [[
    제목, 매물종류, 현장확인일, 요약태그, 보증금, 월세, 계약전용면적, 소재지, 매물특징,
    해당층, 총층, 입주가능일, 월관리비, 방향, 현재업종, 추천업종, 주차가능여부, 총주차대수, 난방,
    용도지역, 건축물용도, article_no, 사용승인일, 매물설명, 중개사, 중개사정보, 중개보수,
    매물사진url, latitude, longitude, 매물링크
]]

with open("naver_office_detailed.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(results)

print(f"✅ 크롤링 완료! 저장된 매물 수: {len(results)}건")
driver.quit()
