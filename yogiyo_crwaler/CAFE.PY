import pandas as pd

# ✅ 파일 경로
file_path = r"C:\Users\Hunae\Downloads\07_24_04_P_CSV\fulldata_07_24_04_P_일반음식점.csv"

# ✅ 메모리 오류 방지: 컬럼 일부만 불러오고 인코딩도 cp949로
use_cols = ['사업장명', '위생업태명', '인허가일자', '영업상태명', '소재지전체주소']
chunksize = 100_000  # 10만 건씩 나눠 불러오기

cafe_keywords = ['커피', '카페']
cafe_dfs = []

print("🔍 카페 업소 추출 중...")

for chunk in pd.read_csv(file_path, encoding='cp949', usecols=use_cols, chunksize=chunksize):
    chunk = chunk.dropna(subset=['위생업태명'])  # 업태명이 없는 행 제거
    cafe_chunk = chunk[chunk['위생업태명'].str.contains('|'.join(cafe_keywords), na=False)]
    cafe_dfs.append(cafe_chunk)

# ✅ 결과 합치기
df_cafe = pd.concat(cafe_dfs, ignore_index=True)

# ✅ 결과 요약
print(f"\n✅ 추출된 카페 업소 수: {len(df_cafe):,}개")
print(df_cafe.head(10))

# ✅ 원하면 저장도 가능
# df_cafe.to_csv("전국_카페_업소_추출본.csv", index=False, encoding='utf-8-sig')
