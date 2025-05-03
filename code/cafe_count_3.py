import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm, rc
import seaborn as sns
from shapely.geometry import Point

# ------------------ 0. 한글 폰트 설정 ------------------ #
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_prop = fm.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())
plt.rcParams['axes.unicode_minus'] = False

# ------------------ 1. 카페 데이터 로드 ------------------ #
df_stores = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\상가정보\소상공인시장진흥공단_상가(상권)정보_서울_202412.csv')
df_cafes = df_stores[(df_stores['시도명'] == '서울특별시') & 
                     (df_stores['상권업종소분류코드'] == 'I21201')].copy()

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

# 면적 단위 확인 및 NaN 방지
gdf_seoul['RELM_AR'] = pd.to_numeric(gdf_seoul['RELM_AR'], errors='coerce')
gdf_seoul = gdf_seoul.dropna(subset=['RELM_AR'])

# ------------------ 3. 상권 이름 데이터 불러오기 ------------------ #
df_population = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\서울시 상권분석서비스(길단위인구-상권).csv', encoding='euc-kr')
df_market_names = df_population[['상권_코드', '상권_코드_명']].drop_duplicates()
df_market_names.rename(columns={'상권_코드': 'TRDAR_CD', '상권_코드_명': 'TRDAR_CD_N'}, inplace=True)
df_market_names['TRDAR_CD'] = df_market_names['TRDAR_CD'].astype(str)

# ------------------ 4. Spatial Join (카페 ↔ 상권) ------------------ #
gdf_joined_all = gpd.sjoin(gdf_cafes, gdf_seoul[['TRDAR_CD', 'geometry']], how='inner', predicate='within')

# ------------------ (1) 중복 상가업소번호 제거 ------------------ #
# 거리 계산 전 EPSG:5179로 좌표계 변환
gdf_seoul_projected = gdf_seoul.to_crs(epsg=5179)
gdf_seoul_centroid = gdf_seoul_projected.copy()
gdf_seoul_centroid['center'] = gdf_seoul_centroid.geometry.centroid

# 카페-상권 후보군에 중심점 거리 계산
gdf_joined_all = gpd.sjoin(gdf_cafes.to_crs(epsg=5179), gdf_seoul_projected[['TRDAR_CD', 'geometry']], how='inner', predicate='within')
gdf_joined_all = pd.merge(gdf_joined_all, gdf_seoul_centroid[['TRDAR_CD', 'center']], on='TRDAR_CD', how='left')
gdf_joined_all['거리'] = gdf_joined_all.geometry.distance(gdf_joined_all['center'])

# 거리 기준으로 같은 상가업소번호 중 가장 가까운 상권만 남김
gdf_joined = gdf_joined_all.sort_values(by='거리').drop_duplicates(subset='상가업소번호', keep='first')

# ------------------ 5. 상권별 카페 수 계산 ------------------ #
df_count = gdf_joined.groupby('TRDAR_CD').size().reset_index(name='카페_점포_수')
df_count['TRDAR_CD'] = df_count['TRDAR_CD'].astype(str)

# ------------------ 6. 상권 이름 및 면적 병합 + 단위면적당 카페수 ------------------ #
df_result = pd.merge(df_count, df_market_names, on='TRDAR_CD', how='left')
df_result = pd.merge(df_result, gdf_seoul[['TRDAR_CD', 'RELM_AR']], on='TRDAR_CD', how='left')

# 단위면적당 카페수 (per 1,000㎡)
df_result['단위면적당_카페수'] = df_result['카페_점포_수'] / (df_result['RELM_AR'] / 1000)

# 컬럼 정리
df_result = df_result[['TRDAR_CD', 'TRDAR_CD_N', '카페_점포_수', 'RELM_AR', '단위면적당_카페수']]

# 저장
df_result.to_csv('상권별_카페_점포_수_0502.csv', index=False, encoding='euc-kr')

# ------------------ 7. 각 카페 점포별 상권 코드/이름 매핑 ------------------ #
# 상가정보.csv 파일에 있는 모든 정보 다 가져와서 저장하려고 함
columns = [
    '상가업소번호', '상호명', '지점명', 'TRDAR_CD', 'TRDAR_CD_N',
    '상권업종소분류코드', '상권업종소분류명', '시도코드', '시도명', '시군구코드', '시군구명',
    '행정동코드', '행정동명', '법정동코드', '법정동명', '지번코드', '대지구분코드',
    '대지구분명', '지번본번지', '지번부번지', '지번주소', '도로명코드', '도로명',
    '건물본번지', '건물부번지', '건물관리번호', '건물명', '도로명주소', '신우편번호',
    '동정보', '층정보', '호정보', '경도', '위도'
]
df_cafes_with_area = gdf_joined[['상가업소번호', '상호명', '지점명', 'TRDAR_CD']].copy()
df_cafes_with_area['TRDAR_CD'] = df_cafes_with_area['TRDAR_CD'].astype(str)
df_cafes_with_area = pd.merge(df_cafes_with_area, df_market_names, on='TRDAR_CD', how='left')

df_cafes_with_area.to_csv('카페_상권_매핑_데이터.csv', index=False, encoding='euc-kr')

# ------------------ 8. 시각화: 상권별 카페 점포 수 Top 10 ------------------ #
sns.set(style="whitegrid")
top10 = df_result.sort_values(by='카페_점포_수', ascending=False).head(10)

plt.figure(figsize=(12, 6))
# hue를 x로 설정하여 FutureWarning 해결
barplot = sns.barplot(data=top10, x='TRDAR_CD_N', y='카페_점포_수', palette="viridis", hue='TRDAR_CD_N', errorbar=None, legend=False)
plt.title('상권별 카페 점포 수 Top 10', fontsize=16, fontproperties=font_prop)
plt.xlabel('상권명', fontproperties=font_prop)
plt.ylabel('카페 점포 수', fontproperties=font_prop)
plt.xticks(rotation=45, ha='right', fontproperties=font_prop)

for bar in barplot.patches:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.0f}', 
             ha='center', va='bottom', fontproperties=font_prop)

plt.tight_layout()
plt.savefig('상권별 카페 점포 수 Top 10.png')
plt.show()

# ------------------ 9. 시각화: 단위면적당 카페 수 Top 10 ------------------ #
top10_density = df_result.sort_values(by='단위면적당_카페수', ascending=False).head(10)

plt.figure(figsize=(12, 6))
# hue를 x로 설정하여 FutureWarning 해결
density_plot = sns.barplot(data=top10_density, x='TRDAR_CD_N', y='단위면적당_카페수', palette="magma", hue='TRDAR_CD_N', errorbar=None, legend=False)
plt.title('상권별 단위면적당 카페 수 Top 10 (per 1,000㎡)', fontsize=16, fontproperties=font_prop)
plt.xlabel('상권명', fontproperties=font_prop)
plt.ylabel('단위면적당 카페 수', fontproperties=font_prop)
plt.xticks(rotation=45, ha='right', fontproperties=font_prop)

for bar in density_plot.patches:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.05, f'{height:.2f}', 
             ha='center', va='bottom', fontproperties=font_prop)

plt.tight_layout()
plt.savefig('상권별 단위면적당 카페 수 Top 10 (per 1,000㎡).png')
plt.show()
