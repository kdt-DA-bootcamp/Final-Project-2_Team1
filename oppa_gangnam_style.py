from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re
import json
from datetime import datetime
import os

# 브라우저 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless=new")  # 💡 headless 브라우저 사용
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(options=options)

# 실패한 동 저장용 리스트
failed_dongs = []

# 제외할 동 목록
exclude_dongs = [
      
       ]

# 페이지 접속 및 초기 설정
# ✅ 강남구 개포동 중심 좌표로 수정
driver.get("https://new.land.naver.com/offices?ms=37.482968,127.0634,16&a=SG&e=RETAIL")
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.area.is-selected")))

# STEP 1. 현재 동(span.area.is-selected) 클릭해서 동 리스트 열기
try:
    current_dong_span = None
    spans = driver.find_elements(By.CSS_SELECTOR, "span.area.is-selected")
    for span in spans:
        if "동" in span.text:
            current_dong_span = span
            break

    if current_dong_span:
        print(f"📍 현재 동: {current_dong_span.text} → 동 리스트 열기 클릭")
        current_dong_span.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.area_list_wrap")))
    else:
        raise Exception("동 선택 영역(span.area.is-selected) 찾지 못함")

except Exception as e:
    print(f"❌ 동 리스트 열기 실패: {e}")
    driver.quit()
    exit()

# STEP 2. 동 리스트 수집
try:
    dong_labels = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "div.area_list_wrap.add_button label.radio_label_district")
    ))
    dong_names_all = [label.text.strip() for label in dong_labels if "동" in label.text]
    dong_names = [name for name in dong_names_all if name not in exclude_dongs]
    print(f"✅ 전체 동 수집 완료 ({len(dong_names)}개): {dong_names}")

except Exception as e:
    print(f"❌ 동 수집 실패: {e}")
    driver.quit()
    exit()

# 크롤링 결과 저장 디렉토리
if not os.path.exists("dong_results"):
    os.makedirs("dong_results")

# STEP 3. 각 동 순회 및 매물 크롤링
for dong_name in dong_names:
    try:
        driver.quit()
        driver = webdriver.Chrome(options=options)
        driver.get("https://new.land.naver.com/offices?ms=37.482968,127.0634,16&a=SG&e=RETAIL")
        wait = WebDriverWait(driver, 10)

        print(f"\n🔁 '{dong_name}' 선택 시도 중...")

        # 동 리스트 열기 → 해당 동 클릭
        spans = driver.find_elements(By.CSS_SELECTOR, "span.area.is-selected")
        for span in spans:
            if "동" in span.text:
                span.click()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.area_list_wrap")))
                break

        label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[text()='{dong_name}']")))
        driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -100);", label)
        time.sleep(0.6)
        driver.execute_script("arguments[0].click();", label)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item_list")))

        # 이후 크롤링 코드 계속...
        # 👇 아래 내용은 그대로 사용 (get_text, extract_value_from_table 등)


        # 스크롤하여 모든 매물 로드
        scroll_container = driver.find_element(By.CSS_SELECTOR, "div.item_list.item_list--article")
        last_count = 0
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
            time.sleep(1.2)
            items = driver.find_elements(By.CSS_SELECTOR, "div.item")
            print(f"🔄 현재 매물 수: {len(items)}개")
            if len(items) == last_count:
                break
            last_count = len(items)

        print(f"🔍 '{dong_name}' 최종 매물 수: {len(items)}개")

        results = []
        for idx in range(len(items)):
            try:
                item = driver.find_elements(By.CSS_SELECTOR, "div.item")[idx]
                link = item.find_element(By.CSS_SELECTOR, "a.item_link")
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                driver.execute_script("arguments[0].click();", link)
                time.sleep(1.5)

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

                article_no = driver.current_url.split("articleNo=")[-1]
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
                            response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                            body = response.get("body", "")
                            data = json.loads(body)
                            addition = data.get("articleAddition", {})
                            latitude = addition.get("latitude", "")
                            longitude = addition.get("longitude", "")
                            break
                    except:
                        continue

                제목 = get_text("span.text")
                거래방식 = get_text("div.info_article_price span.type")
                가격_raw = get_text("div.info_article_price span.price")
                평당가 = get_text("div.info_article_price span.price_per-pyeong")
                보증금, 월세 = (가격_raw.split("/") + [""])[:2] if 거래방식 == "월세" else (가격_raw, "")

                매물확인날짜 = get_text("span.label--confirm em.data")
                요약태그 = ", ".join([el.text.strip() for el in item.find_elements(By.CSS_SELECTOR, "div.tag_area span.tag")])
                계약전용면적 = extract_value_from_table("계약/전용면적")
                층수_raw = extract_value_from_table("해당층/총층")
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
                사용승인일 = extract_value_from_table("사용승인일")
                매물설명 = get_text("tr.info_table_item pre")
                중개사 = get_text("div.table_td_agent strong.info_title")
                중개사정보 = get_text("div.info_agent_wrap")
                중개보수금액 = get_text("strong.point5")
                중개보수요율 = get_text("em.quadrant_value")
                중개보수 = f"{중개보수금액} / {중개보수요율}" if 중개보수금액 else ""
                style_attr = get_text("button.main_photo_item", attr="style")
                img_url_match = re.search(r'url\("(.*?)"\)', style_attr)
                매물사진url = img_url_match.group(1) if img_url_match else ""
                매물링크 = f"https://new.land.naver.com/offices?articleNo={article_no}"
                중개사_결합 = f"{중개사} - {중개사정보}"

                results.append([
                    len(items), 제목, 거래방식, 보증금, 평당가, 월세, 매물확인날짜, 요약태그, 계약전용면적, 소재지,
                    매물특징, 층수_raw, 입주가능일, 월관리비, 방향,
                    현재업종, 추천업종, 주차가능여부, 총주차대수, 난방,
                    용도지역, 건축물용도, article_no, 사용승인일, 매물설명,
                    중개사_결합, 중개보수, 매물사진url, latitude, longitude, 매물링크
                ])

                print(f"✅ {idx+1}번째 매물 수집 완료")

            except Exception as e:
                print(f"❌ {idx+1}번째 매물 크롤링 실패: {e}")

        # 저장
        columns = [
            "전체 매물 수", "제목", "거래방식", "보증금", "평당가", "월세", "매물 확인 날짜", "요약", "계약/전용면적", "소재지",
            "매물특징", "해당층/총층", "입주가능일", "월관리비", "방향",
            "현재업종", "추천업종", "주차가능여부", "총주차대수", "난방(방식/연료)",
            "용도지역", "건축물용도", "매물번호", "사용승인일", "매물설명",
            "중개사 정보", "중개보수", "매물사진url", "위도", "경도", "매물링크"
        ]

        file_path = f"dong_results/{dong_name}.csv"
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(results)

        print(f"📄 '{dong_name}' 매물 저장 완료 → {file_path}")

    except Exception as e:
        print(f"❌ '{dong_name}' 전체 처리 실패: {e}")
        failed_dongs.append(dong_name)

# 실패한 동 저장
if failed_dongs:
    with open("dong_results/failed_dongs.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["실패한 동"])
        for name in failed_dongs:
            writer.writerow([name])
    print(f"\n📄 선택 실패한 동 {len(failed_dongs)}개 → dong_results/failed_dongs.csv로 저장됨")

print("\n🎉 모든 동 매물 크롤링 완료!")
driver.quit()
