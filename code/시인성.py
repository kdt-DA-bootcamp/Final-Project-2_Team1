import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Point
import pandas as pd

# 1. 건물 데이터 불러오기 및 정리
gdf_building = gpd.read_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\전체건물정보\AL_D010_11_20250404.shp',
    engine="pyogrio",
    columns=["A2", "A3", "A5", "A12", "geometry"]
)
gdf_building.rename(columns={'A2': '고유번호', 'A3': '법정동코드', 'A5': '지번', 'A12': '건축물면적(㎡)'}, inplace=True)

# 중복 제거 (면적 큰 건물 우선)
gdf_building = gdf_building.sort_values('건축물면적(㎡)', ascending=False)
gdf_building = gdf_building.drop_duplicates(subset=['법정동코드', '지번'], keep='first')

# 2. 도로 데이터 불러오기 및 정리
gdf_road = gpd.read_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\도로정보\TL_SPRD_RW_11_202504_fixed.shp')
gdf_road.rename(columns={'OPERT_DE': '작업일시', 'RW_SN': '실폭도로일련번호', 'SIG_CD': '시군구코드'}, inplace=True)

# 좌표계 맞추기
gdf_road = gdf_road.to_crs(gdf_building.crs)

# ─────────────────────────────────────────────────────────
# ✅ 시인성 요소 1: 도로와 접한 외곽선 길이 계산
# ─────────────────────────────────────────────────────────

gdf_building['외곽선'] = gdf_building.geometry.boundary
building_boundary = gpd.GeoDataFrame(gdf_building[['법정동코드', '지번']], geometry=gdf_building['외곽선'], crs=gdf_building.crs)

# overlay로 건물 외곽선과 도로 교차 구간 추출 (최적화된 keep_geom_type=False 사용)
intersect = gpd.overlay(building_boundary, gdf_road, how='intersection', keep_geom_type=False)
intersect['접한길이_m'] = intersect.length

# 법정동코드+지번별로 합산 후 merge
접한길이 = intersect.groupby(['법정동코드', '지번'])['접한길이_m'].sum().reset_index()
gdf_building = gdf_building.merge(접한길이, on=['법정동코드', '지번'], how='left')
gdf_building['접한길이_m'] = gdf_building['접한길이_m'].fillna(0)

# ─────────────────────────────────────────────────────────
# ✅ 시인성 요소 2: 교차로 반경 50m 이내 존재 여부
# ─────────────────────────────────────────────────────────
# 도로 선들을 spatial index로 가속화된 교차점 탐색
intersection_points = set()
sindex = gdf_road.sindex

for idx, geom in enumerate(gdf_road.geometry):
    possible_matches_index = list(sindex.intersection(geom.bounds))
    for j in possible_matches_index:
        if idx >= j:
            continue  # 중복 제거
        other = gdf_road.geometry.iloc[j]
        if geom.intersects(other):
            inter = geom.intersection(other)
            if isinstance(inter, Point):
                intersection_points.add(inter)
            elif inter.geom_type == 'MultiPoint':
                intersection_points.update(inter.geoms)

# 교차점 GeoDataFrame 생성
gdf_intersections = gpd.GeoDataFrame(geometry=list(intersection_points), crs=gdf_road.crs)

# 건물 중심점 계산
gdf_building['건물중심'] = gdf_building.geometry.centroid

# 교차점이 존재할 경우 거리 계산
if not gdf_intersections.empty:
    gdf_intersections_sindex = gdf_intersections.sindex
    def is_near_intersection(geom):
        possible = list(gdf_intersections_sindex.intersection(geom.buffer(50).bounds))
        return any(geom.distance(gdf_intersections.geometry.iloc[i]) <= 50 for i in possible)
    gdf_building['교차로_50m이내'] = gdf_building['건물중심'].apply(is_near_intersection)
else:
    gdf_building['교차로_50m이내'] = False

# ─────────────────────────────────────────────────────────
# ✅ 결과 저장
# ─────────────────────────────────────────────────────────
output = gpd.GeoDataFrame(
    gdf_building[['법정동코드', '지번', '고유번호', '접한길이_m', '교차로_50m이내']],
    geometry=gdf_building.geometry,
    crs=gdf_building.crs
)
output.to_file('건물_시인성정보.geojson', driver='GeoJSON')
