import pandas as pd
import os
import glob

# 📁 폴더 경로 설정
folder_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\dong_results\cortarNO"
all_files = glob.glob(os.path.join(folder_path, "*_동별_cortarNo.csv"))

# 📦 데이터 병합
df_list = []
for file in all_files:
    df = pd.read_csv(file)
    # 파일명에서 구 이름 추출 (예: '광진구_동별_cortarNo.csv' → '광진구')
    gu_name = os.path.basename(file).split("_")[0]
    df["구이름"] = gu_name
    df_list.append(df)

merged_df = pd.concat(df_list, ignore_index=True)

# 💡 혹시라도 중복 row가 있다면 제거
merged_df.drop_duplicates(inplace=True)

# ✅ 저장
save_path = os.path.join(folder_path, "서울시_법정동_cortarNo.csv")
merged_df.to_csv(save_path, index=False, encoding="utf-8-sig")
print(f"\n📄 저장 완료: {save_path}")
print(f"✅ 총 수집된 동 개수: {len(merged_df)}개")
