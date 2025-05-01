import os
import pandas as pd
from tqdm import tqdm

# 💾 폴더 경로 설정
base_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\요기요\my_yogiyo\카페디저트_좌표별데이터_전체컬럼(0.01버전)"

# 🗂 전체 CSV 파일 리스트 가져오기
csv_files = [file for file in os.listdir(base_path) if file.endswith('.csv')]

# 📦 전체 DataFrame 담을 리스트
all_dfs = []

# 🔄 파일 하나씩 읽어오기
for file in tqdm(csv_files, desc="📂 CSV 파일 병합 중"):
    file_path = os.path.join(base_path, file)
    try:
        df = pd.read_csv(file_path)
        all_dfs.append(df)
    except Exception as e:
        print(f"❌ {file} 읽기 실패: {e}")

# 🔗 하나로 합치기
merged_df = pd.concat(all_dfs, ignore_index=True)

# 🧹 중복 제거 (id 기준으로)
if 'id' in merged_df.columns:
    dedup_df = merged_df.drop_duplicates(subset='id', keep='first')
else:
    print("⚠️ 'id' 컬럼이 없습니다. 중복 제거가 불가능합니다.")
    dedup_df = merged_df

# 💾 저장 경로
output_path = os.path.join(base_path, "요기요_카페디저트_통합_중복제거.csv")
dedup_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"✅ 저장 완료: {output_path}")
print(f"📊 원본 총 {len(merged_df)}개 → 중복 제거 후 {len(dedup_df)}개")
