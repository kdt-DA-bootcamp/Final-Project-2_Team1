import geopandas as gpd
from shapely.geometry import LineString
from tqdm import tqdm

# ──────────────────────────────────────────────
# 1. 데이터 불러오기
# ──────────────────────────────────────────────
# 건물 폴리곤
gdf_building = gpd.read_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\전체건물정보\AL_D010_11_20250404.shp',
    engine="pyogrio",
    columns=["A2", "A3", "A5", "A12", "geometry"]
)
gdf_building.rename(columns={'A2': '고유번호', 'A3': '법정동코드', 'A5': '지번', 'A12': '건축물면적(㎡)'}, inplace=True)
gdf_building['고유번호'] = gdf_building['고유번호'].astype(str)

# 도로 라인
gdf_road = gpd.read_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\도로정보\TL_SPRD_RW_11_202504_fixed.shp'
)
gdf_road = gdf_road.to_crs(gdf_building.crs)

# ──────────────────────────────────────────────
# 2. 접촉 길이 계산 (intersection)
# ──────────────────────────────────────────────
gdf_building['외곽선'] = gdf_building['geometry'].boundary
building_boundaries = gpd.GeoDataFrame(gdf_building[['고유번호']], geometry=gdf_building['외곽선'], crs=gdf_building.crs)

intersect = gpd.overlay(building_boundaries, gdf_road, how='intersection', keep_geom_type=False)
intersect['접한길이_m'] = intersect.length

접한길이 = intersect.groupby('고유번호')['접한길이_m'].sum().reset_index()
gdf_building = gdf_building.merge(접한길이, on='고유번호', how='left')
gdf_building['접한길이_m'] = gdf_building['접한길이_m'].fillna(0)

# ──────────────────────────────────────────────
# 3. 도로 2m 이내 외곽선 근접 길이 계산
# ──────────────────────────────────────────────
도로_union = gdf_road.unary_union
도로접촉길이_list = []

for geom in tqdm(gdf_building['geometry'], desc="도로 2m 이내 근접 외곽선 길이 계산"):
    if geom is None:
        도로접촉길이_list.append(0.0)
        continue

    접촉길이 = 0.0

    # 단일 Polygon 또는 MultiPolygon 모두 처리
    if geom.geom_type == 'Polygon':
        polygons = [geom]
    elif geom.geom_type == 'MultiPolygon':
        polygons = list(geom.geoms)
    else:
        도로접촉길이_list.append(0.0)
        continue

    for poly in polygons:
        exterior = poly.exterior
        coords = list(exterior.coords)

        for i in range(len(coords) - 1):
            segment = LineString([coords[i], coords[i + 1]])
            if segment.length == 0:
                continue
            if segment.distance(도로_union) <= 2.0:
                접촉길이 += segment.length

    도로접촉길이_list.append(접촉길이)

gdf_building['도로2m이내접촉길이_m'] = 도로접촉길이_list

# ──────────────────────────────────────────────
# 4. 결과 저장
# ──────────────────────────────────────────────
output = gdf_building[['고유번호', '법정동코드', '지번', '건축물면적(㎡)', '접한길이_m', '도로2m이내접촉길이_m', 'geometry']]
output.to_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\건물_도로_시인성_분석.geojson', driver='GeoJSON')

# WKT 변환 및 CSV 저장
output_wkt = output.copy()
output_wkt['geometry'] = output_wkt['geometry'].to_wkt()
output_wkt.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\건물_도로_시인성_분석.csv', index=False, encoding='utf-8-sig')
