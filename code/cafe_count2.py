import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm, rc
import seaborn as sns

# 한글 폰트 설정
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'  # 폰트 경로 확인
font_prop = fm.FontProperties(fname=font_path)

# 한글 폰트를 rc 설정에 적용
rc('font', family=font_prop.get_name())
plt.rcParams['axes.unicode_minus'] = False


# 1. 카페 데이터 로드 및 GeoDataFrame 변환
df_stores = pd.read_csv('./Yesha/소상공인시장진흥공단_상가(상권)정보_서울_202412.csv')
df_cafes = df_stores[(df_stores['시도명'] == '서울특별시') & (df_stores['상권업종소분류코드'] == 'I21201')]
gdf_cafes = gpd.GeoDataFrame(
    df_cafes,
    geometry=gpd.points_from_xy(df_cafes['경도'], df_cafes['위도']),
    crs='EPSG:4326'
)

# 2. 상권 영역 shp 파일 불러오기
gdf_seoul = gpd.read_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\상권_행정구역_구분\서울시 상권분석서비스(영역-상권).shp',
    encoding='euc-kr'
)
if gdf_seoul.crs != 'EPSG:4326':
    gdf_seoul = gdf_seoul.to_crs('EPSG:4326')

# 3. 상권 이름 불러오기
df_population = pd.read_csv('./Yesha/서울시 상권분석서비스(길단위인구-상권).csv', encoding='euc-kr')
df_market_names = df_population[['상권_코드', '상권_코드_명']].drop_duplicates()
df_market_names.rename(columns={'상권_코드': 'TRDAR_CD', '상권_코드_명': 'TRDAR_CD_N'}, inplace=True)

# 💡 타입 통일
df_market_names['TRDAR_CD'] = df_market_names['TRDAR_CD'].astype(str)

# 4. 카페 ↔ 상권 Spatial Join
gdf_joined = gpd.sjoin(gdf_cafes, gdf_seoul, how='inner', predicate='within')

# 5. 카페 수 집계
df_count = gdf_joined.groupby('TRDAR_CD').size().reset_index(name='카페_점포_수')
df_count['TRDAR_CD'] = df_count['TRDAR_CD'].astype(str)  # 💡 타입 통일

# 6. 상권 이름 병합
df_result = pd.merge(df_count, df_market_names, on='TRDAR_CD', how='left')
df_result = df_result[['TRDAR_CD', 'TRDAR_CD_N', '카페_점포_수']]

# 7. 저장 (한글깨짐 방지를 위해 euc-kr)
df_result.to_csv('./Yesha/상권별_카페_점포_수.csv', index=False, encoding='euc-kr')

# 결과 확인
print(df_result.head(3))


#### 시각화 ####

# 상위 10개 추출
top10 = df_result.sort_values(by='카페_점포_수', ascending=False).head(10)

# Seaborn 스타일 설정
sns.set(style="whitegrid", palette="muted")

# 시각화
plt.figure(figsize=(12, 6), dpi = 300)

# Seaborn barplot (여기에는 fontproperties 사용하지 않음!)
bars = sns.barplot(data=top10, x='TRDAR_CD_N', y='카페_점포_수', palette="viridis", ci=None)

# 타이틀 및 라벨 (여기서 fontproperties 적용)
plt.title('상권별 카페 점포 수 Top 10', fontsize=16, fontproperties=font_prop)
plt.xlabel('상권명', fontproperties=font_prop)
plt.ylabel('카페 점포 수', fontproperties=font_prop)

# x축 tick에도 폰트 적용
for label in bars.get_xticklabels():
    label.set_fontproperties(font_prop)

# 값 표시
for bar in bars.patches:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 1, f'{height:.0f}',
             ha='center', va='bottom', fontproperties=font_prop, fontsize=10)

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('./Yesha/상권별 카페 점포 수 Top 10.png')
plt.show()
