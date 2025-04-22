import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 💾 CSV 경로
csv_dir = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results"

# 🌐 브라우저 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# ✅ 접속
driver.get("https://new.land.naver.com/offices?ms=37.5377974,127.0020821,15&a=SG&e=RETAIL")
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.area.is-selected")))

# 🧭 동 리스트 열기
spans = driver.find_elements(By.CSS_SELECTOR, "span.area.is-selected")
for span in spans:
    if "동" in span.text:
        span.click()
        break
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.area_list_wrap")))

# 📌 동 이름 수집
dong_labels = driver.find_elements(By.CSS_SELECTOR, "div.area_list_wrap.add_button label.radio_label_district")
dong_names = [label.text.strip() for label in dong_labels if "동" in label.text]
print(f"🔍 전체 동 수집 완료 ({len(dong_names)}개): {dong_names}")

# 📊 비교 결과 리스트
comparison = []

# 🔁 각 동 매물 수 확인
for dong_name in dong_names:
    try:
        # 동 리스트 열기
        spans = driver.find_elements(By.CSS_SELECTOR, "span.area.is-selected")
        for span in spans:
            if "동" in span.text:
                span.click()
                break
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.area_list_wrap")))

        label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[text()='{dong_name}']")))
        driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -100);", label)
        time.sleep(0.4)
        driver.execute_script("arguments[0].click();", label)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item_list")))

        # 스크롤하여 전체 매물 로드
        scroll_container = driver.find_element(By.CSS_SELECTOR, "div.item_list.item_list--article")
        last_count = 0
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
            time.sleep(1.2)
            items = driver.find_elements(By.CSS_SELECTOR, "div.item")
            if len(items) == last_count:
                break
            last_count = len(items)

        actual_count = len(items)

        # 로컬 CSV 파일 개수 확인
        csv_file = os.path.join(csv_dir, f"{dong_name}.csv")
        saved_count = len(pd.read_csv(csv_file)) if os.path.exists(csv_file) else 0

        comparison.append([dong_name, saved_count, actual_count, actual_count - saved_count])
        print(f"✅ {dong_name}: 저장 {saved_count}, 실제 {actual_count}, 차이 {actual_count - saved_count}")

    except Exception as e:
        print(f"❌ {dong_name} 실패: {e}")
        comparison.append([dong_name, "오류", "오류", "오류"])

# 🔚 종료 및 저장
driver.quit()

# 결과 저장
df_result = pd.DataFrame(comparison, columns=["동이름", "CSV_저장개수", "실제_매물수", "차이"])
save_path = os.path.join(csv_dir, "매물수_비교결과.csv")
df_result.to_csv(save_path, index=False, encoding="utf-8-sig")
print(f"\n📄 결과 저장 완료 → {save_path}")
