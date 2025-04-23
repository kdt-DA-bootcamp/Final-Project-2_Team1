import requests
import json
import pandas as pd
import time
import os

# 🔐 네이버 부동산 Authorization 토큰
auth_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NDUzMDgzODEsImV4cCI6MTc0NTMxOTE4MX0.P7JjaluVbksSqwjv9lEsfErW-03drDYf4LaoN3Zy1iU"

headers = {
    "Authorization": auth_token.strip(),
    "Referer": "https://new.land.naver.com/offices?cortarNo=1144010500",
    "User-Agent": "Mozilla/5.0"
}

# 📁 cortarNo 파일 경로
csv_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\cortarNO\서울시_법정동_cortarNo.csv"
df = pd.read_csv(csv_path)
fail_list = []

for _, row in df.iterrows():
    gu, dong, cortar_no = row["구이름"], row["동이름"], str(row["cortarNo"])
    print(f"\n🌐 수집 중: [{gu} - {dong}] cortarNo = {cortar_no}")

    all_articles = []
    page = 1

    while True:
        url = (
            f"https://new.land.naver.com/api/articles?"
            f"cortarNo={cortar_no}&order=rank&realEstateType=SG"
            f"&tradeType=&priceType=RETAIL&page={page}"
        )
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                print(f"❌ 요청 실패: {res.status_code}")
                fail_list.append((gu, dong, cortar_no))
                break

            data = res.json().get("articleList", [])
            if not data:
                print("✅ 더 이상 데이터 없음")
                break

            all_articles.extend(data)
            print(f"📦 Page {page} - {len(data)}건 수집됨")
            page += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"⚠️ 예외 발생: {e}")
            fail_list.append((gu, dong, cortar_no))
            break

    # 📊 필요한 컬럼 정리
    cleaned = []
    for article in all_articles:
        area1 = article.get("area1")
        area2 = article.get("area2")
        floor_info = article.get("floorInfo", "")
        해당층, 총층 = None, None
        if "/" in floor_info:
            parts = floor_info.split("/")
            해당층 = parts[0].strip()
            총층 = parts[1].strip()

        전용률 = round(float(area2) / float(area1) * 100, 1) if area1 and area2 else None

        row = {
            "거래방식": article.get("tradeTypeName"),
            "보증금": article.get("dealOrWarrantPrc"),
            "월세": article.get("rentPrc"),
            "계약면적": area1,
            "전용면적": area2,
            "전용률(%)": 전용률,
            "해당층": 해당층,
            "총층": 총층,
            "위도": article.get("latitude"),
            "경도": article.get("longitude")
        }
        cleaned.append(row)

    # 💾 저장
    save_dir = os.path.join("필요컬럼매물", gu)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{dong}.csv")
    pd.DataFrame(cleaned).to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"✅ 저장 완료 → {save_path}")

# ❗ 실패 목록 출력
if fail_list:
    print("\n❗ 수집 실패한 동 목록:")
    for gu, dong, cortar_no in fail_list:
        print(f"- {gu} {dong} (cortarNo: {cortar_no})")

    pd.DataFrame(fail_list, columns=["구이름", "동이름", "cortarNo"]).to_csv(
        "수집실패_동목록.csv", index=False, encoding="utf-8-sig"
    )
    print("📄 '수집실패_동목록.csv' 파일로 저장 완료")
else:
    print("\n🎉 모든 동 매물 정보 수집 성공!")
