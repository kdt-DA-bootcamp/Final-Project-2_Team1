import pandas as pd

df_cafes = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\임대료_추정_최종.csv')
print("중복된 행 수(상호명, 지점명):", df_cafes.duplicated(subset=['상호명','지점명']).sum())
print("중복된 행 수(상호명, 도로명주소):", df_cafes.duplicated(subset=['상호명','도로명주소']).sum())
"""
# 6개 컬럼 기준으로 중복 제거
df_cafes_dedup = df_cafes.drop_duplicates(subset=['상호명',  '도로명주소'], keep='first')

print(df_cafes_dedup.shape)
print(df_cafes_dedup.head())
# df_cafes_dedup.to_csv('카페_상권_매핑_데이터_중복제거.csv', encoding = 'utf-8-sig', index =False)

# 중복된 모든 행 (첫 항목 포함해서 모두 보여줌)
all_duplicates = df_cafes[df_cafes.duplicated(subset=['상호명','도로명주소'], keep=False)]

# 중복 그룹별 개수 세기
grouped_counts = all_duplicates.groupby(['상호명','도로명주소']).size().reset_index(name='중복횟수')

# 중복 횟수가 많은 순으로 정렬
grouped_counts = grouped_counts.sort_values(by='중복횟수', ascending=False)

print(grouped_counts)
"""