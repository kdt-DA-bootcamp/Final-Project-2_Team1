import pandas as pd

# 1) CSV 파일 불러오기
df = pd.read_csv('카페_별점리뷰통합.csv', encoding='utf-8-sig')

# 2) naver_reviewCount, kakao_reviewCount 문자열 → 정수 변환
for col in ['naver_reviewCount', 'kakao_reviewCount']:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(',', '', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
        .astype(int)
    )

# 3) total_reviewCount 계산
df['total_reviewCount'] = df['naver_reviewCount'] + df['kakao_reviewCount']

# 4) naver_score, kakao_score 숫자형으로 변환
df['naver_score'] = pd.to_numeric(df['naver_score'], errors='coerce')
df['kakao_score'] = pd.to_numeric(df['kakao_score'], errors='coerce')

# 5) avg_score 계산
df['avg_score'] = (
    df[['naver_score', 'kakao_score']]
    .mean(axis=1)
    .round(1)
)

# 6) 처리된 데이터 CSV로 저장
output_path = 'merged_seoul_cafes.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')

# 7) 결과 미리보기
print(df[['naver_reviewCount', 'kakao_reviewCount', 'total_reviewCount', 
           'naver_score', 'kakao_score', 'avg_score']].head())

# 사용자에게 저장된 파일 경로 안내
print(f"처리된 결과가 '{output_path}'에 저장되었습니다.")