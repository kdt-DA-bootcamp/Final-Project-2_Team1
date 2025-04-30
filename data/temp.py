# -*- coding: utf-8 -*-
import pandas as pd

df_cafes = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_상권_매핑_데이터_0421.csv')
df_infos = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\상가정보\소상공인시장진흥공단_상가(상권)정보_서울_202412.csv')
df_cafes = df_cafes[['상가업소번호',"상호명",'지점명','TRDAR_CD','TRDAR_CD_N']]
print(df_infos.columns.tolist())
df_add = df_infos[['상가업소번호','상권업종소분류코드', '상권업종소분류명', '시도코드', '시도명', '시군구코드', '시군구명', '행정동코드', '행정동명', '법정동코드', '법정동명', '지번코드', '대지구분코드', '대지구분명', '지번본번지', '지번부번지', '지번주소', '도로명코드', '도로명', '건물본번지', '건물부번지', '건물관리번호', '건물명', '도로명주소', '신우편번호', '동정보', '층정보', '호정보', '경도', '위도']]
print(df_add[['건물본번지','건물관리번호','건물명']].head())
print(f'카페 df 길이: {len(df_cafes)}')
df_merged = pd.merge(df_cafes, df_add, on = '상가업소번호', how = 'left')
print(df_merged.head(5))
print(f'merge df 길이: {len(df_merged)}')
print(df_merged.isna().sum())
df_merged.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data/점수산출/카페_상권_매핑_데이터_0426.csv', index = False, encoding = 'utf-8-sig')