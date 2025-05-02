import pandas as pd
import numpy as np

# 데이터 불러오기
df_score = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수.csv')
df_cafes = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_상권_매핑_데이터_0426.csv')
df_adds = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\seoul_cafes(편의시설).csv')

# 층정보 관련 처리
df_cafes = df_cafes[['상가업소번호', '상호명', '층정보']]
df_cafes['층정보'] = df_cafes['층정보'].fillna('1')
df_cafes['floor_score'] = df_cafes['층정보'].apply(lambda x: 1 if '1' in str(x) else 0)

print(df_cafes.head(4))

# 주차 여부 처리
df_adds = df_adds[['query', 'parking']]
df_adds['parking_score'] = df_adds['parking'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)

print(df_adds.head(4))

df_scores = pd.merge(df_adds, df_cafes[['상가업소번호','상호명','floor_score']], left_on='query',right_on='상호명',how = 'left')
df_merged = pd.merge(df_score, df_scores[['상가업소번호', 'floor_score','parking_score']], on = '상가업소번호', how = 'left')
print(df_merged.head(3))
df_merged.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수.csv', encoding = 'utf-8-sig', index = False)