import os
import pandas as pd

# 입력 폴더 (중복 제거 전)
input_root = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\서울시_상가_전체구"
# 출력 폴더 (중복 제거 후)
output_root = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\서울시_상가_중복제거완료"

# 중복 판단 기준 컬럼
duplicate_cols = ["floorInfo", "area1", "area2", "latitude", "longitude"]
# 남길 기준 컬럼 (확인일 최신)
keep_latest_col = "articleConfirmYmd"

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
            if df.empty:
                print(f"⚠️ 빈 파일 스킵: {file}")
                continue

            if not all(col in df.columns for col in duplicate_cols + [keep_latest_col]):
                print(f"❌ 필요한 컬럼 누락: {file}")
                continue

            # 중복 제거: articleConfirmYmd 기준으로 최신 데이터만 남김
            df[keep_latest_col] = pd.to_numeric(df[keep_latest_col], errors="coerce")
            df = df.sort_values(by=keep_latest_col, ascending=False)
            deduped_df = df.drop_duplicates(subset=duplicate_cols, keep="first")

            # 저장 경로 구성
            output_gu_path = os.path.join(output_root, gu)
            os.makedirs(output_gu_path, exist_ok=True)
            output_path = os.path.join(output_gu_path, file)
            deduped_df.to_csv(output_path, index=False, encoding="utf-8-sig")

            print(f"✅ 저장 완료: {output_path} (중복 제거 전: {len(df)}, 후: {len(deduped_df)})")

        except Exception as e:
            print(f"❌ 처리 실패: {file_path} → {e}")
