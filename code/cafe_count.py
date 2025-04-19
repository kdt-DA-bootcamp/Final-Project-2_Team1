# 상가 정보를 통해, 상권 내 카페 점포의 수가 얼마인지 count
# 장소 표시 시각화

# EDA
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import matplotlib.cm as cm
import numpy as np

# 한글 폰트 설정
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

df_stores = pd.read_csv('./Yesha/소상공인시장진흥공단_상가(상권)정보_서울_202412.csv')

df_cafes = df_stores[(df_stores['시도명'] == '서울특별시') & (df_stores['상권업종소분류코드'] == 'I21201')]
# 위도/경도 좌표로 포인트 생성 → GeoDataFrame으로 변환
gdf_cafes = gpd.GeoDataFrame(
    df_cafes,
    geometry=gpd.points_from_xy(df_cafes['경도'], df_cafes['위도']),
    crs='EPSG:4326'  # GPS 좌표계
)
print(len(df_cafes))
"""
print(f'칼럼: {df_stores.columns}')
칼럼: Index(['상가업소번호', '상호명', '지점명', '상권업종대분류코드', '상권업종대분류명', '상권업종중분류코드',
       '상권업종중분류명', '상권업종소분류코드', '상권업종소분류명', '표준산업분류코드', '표준산업분류명', '시도코드',
       '시도명', '시군구코드', '시군구명', '행정동코드', '행정동명', '법정동코드', '법정동명', '지번코드',
       '대지구분코드', '대지구분명', '지번본번지', '지번부번지', '지번주소', '도로명코드', '도로명', '건물본번지',
       '건물부번지', '건물관리번호', '건물명', '도로명주소', '구우편번호', '신우편번호', '동정보', '층정보',
       '호정보', '경도', '위도']
카페의 대분류 코드 I2
중분류 코드 I212
소분류 코드 I21201
       """
# 경도와 위도를 통해서 상권 지역에 포함되는지 알 수 있을까?

# 서울 상권 지도 영역 불러오기 (SHP 파일)
gdf_seoul = gpd.read_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\상권_행정구역_구분\서울시 상권분석서비스(영역-상권).shp')
# 좌표계 통일
if gdf_seoul.crs != 'EPSG:4326':
    gdf_seoul = gdf_seoul.to_crs('EPSG:4326')
#----------------------------------------------------#

"""# 전체 점 개수 기준으로 컬러맵 색상 생성 (viridis, plasma, etc.)
cmap = cm.get_cmap('tab20', len(gdf_cafes))  # 또는 'viridis', 'nipy_spectral', 'rainbow'

colors = [cmap(i) for i in range(len(gdf_cafes))]

fig, ax = plt.subplots(figsize=(12,8), dpi = 300)

# 서울 상권 경계 그리기
gdf_seoul.boundary.plot(ax=ax, edgecolor='gray', linewidth=0.1)

# 카페 위치 점 찍기
gdf_cafes.plot(ax=ax, color=colors, markersize=0.2, alpha=0.5)

# 타이틀 및 표시 설정
plt.title('서울시 카페 점포 위치 분포', fontsize=12)
plt.axis('off')
plt.savefig('서울시 카페 점포 위치 분포.png')
plt.show()"""

# 각 상권 내의 카페 점포 수를 세려면?

# shp 파일의 상권 코드, 좌표를 가져오기
# 정보 확인 (상권_코드, 상권_코드_명 으로 되어있을 것)
# 어떤 컬럼이 상권 코드/이름인지 먼저 확인
print(gdf_seoul.columns)

# 상권 영역 내 카페 찾기
gdf_cafes_in_market = gpd.sjoin(gdf_cafes, gdf_seoul, how='inner', predicate='within')

# 상권별로 카페 수 집계
df_grouped = gdf_cafes_in_market.groupby(['상권_코드', '상권_코드_명']).size().reset_index(name='카페_점포_수')

# CSV 저장
df_grouped.to_csv('상권별_카페_점포_수.csv', index=False, encoding='utf-8-sig')
