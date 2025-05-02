import pandas as pd
import geopandas as gpd
import fiona
# gpd.options.use_pyogrio = False  # pyogrio 대신 fiona 사용
# 인구 feature 정리


# 총 유동인구 수
df_commercial = gpd.read_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\상권_행정구역_구분\서울시 상권분석서비스(영역-상권).shp', encoding = 'euc-kr') # 한글 없이 상권 코드만 가지고 할 수 있는가?
sub_commercial = df_commercial[['TRDAR_CD', 'RELM_AR','geometry']].head(2)
df_population = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\서울시 상권분석서비스(길단위인구-상권).csv', encoding = 'euc-kr')
print(df_population.columns)
# df_sales = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\서울시 상권분석서비스(추정매출-상권)_2024년.csv',encoding = 'euc-kr')
# print(df_sales.columns)
# 상권 / 매장별로 나눌 수는 없을까?
# 시간대별 유동인구 수 (정제 방법 고민)
population_time = df_population[['상권_코드','상권_코드_명',
                                 '시간대_00_06_유동인구_수', '시간대_06_11_유동인구_수', '시간대_11_14_유동인구_수',
                                 '시간대_14_17_유동인구_수', '시간대_17_21_유동인구_수', '시간대_21_24_유동인구_수']]
# 평일과 주말의 유동인구 차이 (정제 방법 고민, 어떻게 feature로 사용할 수 있을지)
population_day = df_population[['상권_코드','상권_코드_명',
                                '월요일_유동인구_수', '화요일_유동인구_수', '수요일_유동인구_수', '목요일_유동인구_수', '금요일_유동인구_수',
                                '토요일_유동인구_수', '일요일_유동인구_수']]
population_day = population_day.copy()
# test로 유동인구와 매출액 상관성을 볼까 

# 요일별 컬럼 목록
weekday_cols = ['월요일_유동인구_수', '화요일_유동인구_수', '수요일_유동인구_수', '목요일_유동인구_수', '금요일_유동인구_수']
weekend_cols = ['토요일_유동인구_수', '일요일_유동인구_수']

# 그룹별 계산
population_grouped = (
    df_population
    .groupby(['기준_년분기_코드', '상권_코드', '상권_코드_명'])[weekday_cols + weekend_cols]
    .mean()
    .reset_index()
)

# 평균 계산
population_grouped['평균_평일_유동인구_수'] = population_grouped[weekday_cols].sum(axis=1) / 5
population_grouped['평균_주말_유동인구_수'] = population_grouped[weekend_cols].sum(axis=1) / 2
population_grouped['평일_대비_주말_유동인구_비율'] = population_grouped['평균_주말_유동인구_수'] / population_grouped['평균_평일_유동인구_수']

# 최종 정리
populations = population_grouped[['기준_년분기_코드', '상권_코드','상권_코드_명','평균_평일_유동인구_수','평균_주말_유동인구_수','평일_대비_주말_유동인구_비율']]

# 저장
populations.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\calculate_populations_by_quarter.csv', encoding='utf-8-sig', index=False)
