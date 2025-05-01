import pandas as pd

# ✅ 파일 경로
file_path = r"C:\Users\hunae\Downloads\07_24_04_P_CSV\07_24_05_P.xlsx"

# ✅ 엑셀 파일 읽기 (첫 시트 기준)
df_sample = pd.read_excel(file_path, sheet_name=0)

# ✅ 컬럼 목록 출력
print("📌 컬럼 목록:")
print(df_sample.columns.tolist())

# ✅ 상위 10개 샘플 출력
print("\n📌 상위 10개 데이터:")
print(df_sample.head(10))
