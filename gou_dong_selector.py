from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# 브라우저 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# 실패한 동 저장용 리스트
failed_dongs = []

# 페이지 접속 및 초기 설정
driver.get("https://new.land.naver.com/offices?ms=37.5377974,127.0020821,15&a=SG&e=RETAIL")
wait = WebDriverWait(driver, 10)
time.sleep(3)

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
        time.sleep(1.5)
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
    dong_names = [label.text.strip() for label in dong_labels if "동" in label.text]
    print(f"✅ 용산구 전체 동 수집 완료 ({len(dong_names)}개): {dong_names}")

except Exception as e:
    print(f"❌ 동 수집 실패: {e}")
    driver.quit()
    exit()

# STEP 3. 각 동 순회 + 반영 여부 확인 + 실패 시 재시도
for idx, dong_name in enumerate(dong_names):
    print(f"\n🔁 '{dong_name}' 선택 시도 중...")
    try:
        prev_items = driver.find_elements(By.CSS_SELECTOR, "div.item")
        prev_count = len(prev_items)

        def open_dong_list():
            spans = driver.find_elements(By.CSS_SELECTOR, "span.area.is-selected")
            for span in spans:
                if "동" in span.text:
                    span.click()
                    time.sleep(1.5)
                    return
            raise Exception("동 선택 영역 클릭 실패")

        open_dong_list()

        label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[text()='{dong_name}']")))
        driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -100);", label)
        time.sleep(0.6)

        visible = label.is_displayed()
        enabled = label.is_enabled()
        print(f"🔎 is_displayed: {visible}\n🔎 is_enabled: {enabled}\n🔎 class: {label.get_attribute('class')}")

        if not visible:
            print(f"⚠️ '{dong_name}' 안 보이지만 강제 클릭 시도함")
            driver.execute_script("arguments[0].click();", label)
        else:
            label.click()

        # 최대 3회까지 반영 확인 시도
        selected_name = ""
        for attempt in range(3):
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, "a.filter_btn_region span.area.is-selected")[2].text.strip() == dong_name
                )
                break
            except:
                print(f"⏳ 반영 지연, {attempt+1}차 재시도 중...")
                time.sleep(1)
        else:
            # 실패 시 재시도: 동선택창 다시 열고 클릭
            print(f"🔄 '{dong_name}' 재선택 시도 (강제 반영 안 됨)")
            open_dong_list()
            label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[text()='{dong_name}']")))
            driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -100);", label)
            driver.execute_script("arguments[0].click();", label)
            WebDriverWait(driver, 5).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "a.filter_btn_region span.area.is-selected")[2].text.strip() == dong_name
            )

        selected_name = driver.find_elements(By.CSS_SELECTOR, "a.filter_btn_region span.area.is-selected")[2].text.strip()
        if dong_name != selected_name:
            raise Exception(f"선택한 동이 '{dong_name}'인데 반영된 동은 '{selected_name}'")

        current_items = driver.find_elements(By.CSS_SELECTOR, "div.item")
        current_count = len(current_items)
        if prev_count == current_count:
            print(f"⚠️ '{dong_name}' 클릭 후 매물 수 변화 없음 ({prev_count} → {current_count})")
        else:
            print(f"✅ '{dong_name}' 선택 성공 (현재 동: {selected_name}, 매물 수 변화: {prev_count} → {current_count})")

        time.sleep(2.0)

    except Exception as e:
        print(f"❌ '{dong_name}' 선택 실패: {e}")
        failed_dongs.append(dong_name)
        continue

# 실패한 동 CSV로 저장
if failed_dongs:
    with open("failed_dongs.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["실패한 동"])
        for name in failed_dongs:
            writer.writerow([name])
    print(f"\n📄 선택 실패한 동 {len(failed_dongs)}개 → failed_dongs.csv로 저장됨")

print("\n🎉 용산구 전체 동 순회 및 반영 확인 완료!")
driver.quit()
