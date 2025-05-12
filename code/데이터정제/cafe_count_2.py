import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm, rc
import seaborn as sns

# ------------------ 0. 한글 폰트 설정 ------------------ #
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_prop = fm.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())
plt.rcParams['axes.unicode_minus'] = False

# ------------------ 1. 카페 데이터 로드 ------------------ #
df_stores = pd.read_csv('./data/소상공인시장진흥공단_상가(상권)정보_서울_202412.csv')
df_cafes = df_stores[(df_stores['시도명'] == '서울특별시') & 
                     (df_stores['상권업종소분류코드'] == 'I21201')]

# GeoDataFrame 변환
gdf_cafes = gpd.GeoDataFrame(
    df_cafes,
    geometry=gpd.points_from_xy(df_cafes['경도'], df_cafes['위도']),
    crs='EPSG:4326'
)

# ------------------ 2. 상권 영역 shp 파일 불러오기 ------------------ #
gdf_seoul = gpd.read_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\상권_행정구역_구분\서울시 상권분석서비스(영역-상권).shp',
    encoding='euc-kr'
)
if gdf_seoul.crs != 'EPSG:4326':
    gdf_seoul = gdf_seoul.to_crs('EPSG:4326')

# ------------------ 3. 상권 이름 데이터 불러오기 ------------------ #
df_population = pd.read_csv('./data/서울시 상권분석서비스(길단위인구-상권).csv', encoding='euc-kr')
df_market_names = df_population[['상권_코드', '상권_코드_명']].drop_duplicates()
df_market_names.rename(columns={'상권_코드': 'TRDAR_CD', '상권_코드_명': 'TRDAR_CD_N'}, inplace=True)
df_market_names['TRDAR_CD'] = df_market_names['TRDAR_CD'].astype(str)

# ------------------ 4. Spatial Join (카페 ↔ 상권) ------------------ #
gdf_joined = gpd.sjoin(gdf_cafes, gdf_seoul, how='inner', predicate='within')

print(gdf_seoul.columns)

# 각 카페에 상권 코드와 상권 명을 붙임 , 

# 만약 같은 상가업소번호가 중복되는 경우, 어느 상권 중심에 가까운지 계산하여 하나만 남김

# 상권별 카페 수 추출
# 상권별 카페 수 top 10 시각화

# 단위면적 당 카페 수 추출
# 상권별 단위면적당 카페 수 top10 시각화

# ------------------ 5. 카페 수 집계 (상권별) ------------------ #
df_count = gdf_joined.groupby('TRDAR_CD').size().reset_index(name='카페_점포_수')
df_count['TRDAR_CD'] = df_count['TRDAR_CD'].astype(str)

# 상권 이름 병합
df_result = pd.merge(df_count, df_market_names, on='TRDAR_CD', how='left')
df_result = df_result[['TRDAR_CD', 'TRDAR_CD_N', '카페_점포_수']]
df_result.to_csv('./data/상권별_카페_점포_수.csv', index=False, encoding='euc-kr')

# ------------------ 6. 각 카페 점포별 상권 코드/이름 매핑 ------------------ #
df_cafes_with_area = gdf_joined[['상가업소번호', '상호명', '지점명', 'TRDAR_CD']].copy()
df_cafes_with_area['TRDAR_CD'] = df_cafes_with_area['TRDAR_CD'].astype(str)
df_cafes_with_area = pd.merge(df_cafes_with_area, df_market_names, on='TRDAR_CD', how='left')
df_cafes_with_area = df_cafes_with_area[['상가업소번호', '상호명', '지점명', 'TRDAR_CD', 'TRDAR_CD_N']]
df_cafes_with_area.to_csv('./data/카페_상권_매핑_데이터.csv', index=False, encoding='euc-kr')

# ------------------ 7. 시각화: 상권별 카페 점포 수 상위 10 ------------------ #
# Seaborn 스타일
sns.set(style="whitegrid")

# Top 10 추출
top10 = df_result.sort_values(by='카페_점포_수', ascending=False).head(10)

# 시각화
plt.figure(figsize=(12, 6))
barplot = sns.barplot(data=top10, x='TRDAR_CD_N', y='카페_점포_수', palette="viridis", ci=None)

# 라벨 설정
plt.title('상권별 카페 점포 수 Top 10', fontsize=16, fontproperties=font_prop)
plt.xlabel('상권명', fontproperties=font_prop)
plt.ylabel('카페 점포 수', fontproperties=font_prop)
plt.xticks(rotation=45, ha='right', fontproperties=font_prop)

# 값 표시
for bar in barplot.patches:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.0f}', 
             ha='center', va='bottom', fontproperties=font_prop)

plt.tight_layout()
plt.show()