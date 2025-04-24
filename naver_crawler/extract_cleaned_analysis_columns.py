import os
import pandas as pd

# 입력 경로 (중복 제거된 데이터)
input_root = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\2. 서울시_상가_중복제거완료"
# 출력 경로 (필요 컬럼만 추출 후 저장)
output_root = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\서울시_상가_분석데이터"

# 추출할 컬럼
target_cols = [
    "articleNo", "articleName", "tradeTypeName",
    "floorInfo", "rentPrc", "dealOrWarrantPrc",
    "area1", "area2", "direction",
    "articleConfirmYmd", "tagList",
    "latitude", "longitude"
]

for gu in os.listdir(input_root):
    gu_path = os.path.join(input_root, gu)
    if not os.path.isdir(gu_path):
        continue

    for file in os.listdir(gu_path):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(gu_path, file)
        try:
            df = pd.read_csv(file_path, dtype=str)

            # 위도/경도 없는 행 제거
            if "latitude" not in df.columns or "longitude" not in df.columns:
                print(f"❌ 위경도 컬럼 없음 → {file}")
                continue

            df = df.dropna(subset=["latitude", "longitude"])
            df = df[df["latitude"].str.strip() != ""]
            df = df[df["longitude"].str.strip() != ""]
            df = df[~df["latitude"].isin(["0", "0.0"])]
            df = df[~df["longitude"].isin(["0", "0.0"])]

            # 없는 컬럼은 추가해서 NaN으로 채움
            for col in target_cols:
                if col not in df.columns:
                    df[col] = pd.NA

            # 필요한 컬럼만 추출
            df = df[target_cols]

            # 저장 경로
            output_gu_path = os.path.join(output_root, gu)
            os.makedirs(output_gu_path, exist_ok=True)
            output_path = os.path.join(output_gu_path, file)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            print(f"✅ 저장 완료: {output_path} (총 {len(df)}건)")

        except Exception as e:
            print(f"❌ 처리 실패: {file_path} → {e}")
