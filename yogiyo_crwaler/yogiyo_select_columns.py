import pandas as pd
import os

# 📂 입력 파일 경로
input_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\요기요\my_yogiyo\(0.01버전)카페디저트_좌표별데이터_전체컬럼\요기요_카페디저트_통합_중복제거_서울만.csv"

# 💾 출력 파일 경로
output_path = input_path.replace(".csv", "_선별컬럼.csv")

# ✅ 필요한 컬럼 목록
selected_columns = [
    "id", "name", "categories", "review_avg", "review_count",
    "franchise_id", "lat", "lng", "owner_reply_count",
    "begin", "end", "address", "franchise_name"
]

# 📥 파일 로드
df = pd.read_csv(input_path)

# 🧼 컬럼 필터링
filtered_df = df[selected_columns]

# 💾 저장
filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"✅ 지정된 컬럼만 저장 완료: {output_path}")
print(f"🧮 저장된 컬럼 수: {len(filtered_df.columns)}개, 행 수: {len(filtered_df)}개")
