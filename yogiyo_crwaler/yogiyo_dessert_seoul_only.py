import pandas as pd
import os

# 📂 파일 경로
file_path = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\요기요\my_yogiyo\(0.01버전)카페디저트_좌표별데이터_전체컬럼\요기요_카페디저트_통합_중복제거.csv"

# 💾 저장 경로
output_path = file_path.replace(".csv", "_서울만.csv")

# 📥 데이터 로드
df = pd.read_csv(file_path)

# 🧹 '서울특별시'로 시작하는 address만 필터링
df_seoul = df[df['address'].str.startswith("서울특별시", na=False)]

# 💾 결과 저장
df_seoul.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"✅ 서울만 남긴 데이터 저장 완료: {output_path}")
print(f"📊 기존: {len(df)}개 → 서울: {len(df_seoul)}개")
