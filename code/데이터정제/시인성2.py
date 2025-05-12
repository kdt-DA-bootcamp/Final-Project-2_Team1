import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

# 교차로와 건물 데이터 불러오기
cross = gpd.read_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\교차로정보\A008_P.shp')
building_copy = gpd.read_file(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\건물_도로_시인성_분석.geojson')

# 거리 계산을 위한 투영 좌표계 (서울 기준)
projected_crs = "EPSG:5186"
building_copy_proj = building_copy.to_crs(projected_crs)
cross_proj = cross.to_crs(projected_crs)

# 건물마다 반경 30m 버퍼 생성
building_buffer = building_copy_proj.copy()
building_buffer["geometry"] = building_buffer.buffer(50)

# 공간 조인: 버퍼 내에 교차로가 포함되는지 확인
joined = gpd.sjoin(building_buffer, cross_proj, how="left", predicate='contains')

# 교차로가 하나라도 포함되면 True
# 'index_right'는 교차로가 포함되었을 때만 값이 존재
contains_cross = joined.index_right.notnull()
contains_cross_by_building = contains_cross.groupby(joined.index).any()

# 기존 building_copy와 index를 맞춰서 새로운 컬럼 추가
building_copy["교차로_존재_여부"] = building_copy.index.map(contains_cross_by_building).fillna(False)

# 결과 확인
print(building_copy["교차로_존재_여부"].value_counts())

# GeoJSON으로 저장 (공간 정보 포함)
building_copy.to_file(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\건물_도로_시인성_분석_0509.geojson',
    driver='GeoJSON'
)

# CSV로 저장 (공간 정보 제외)
building_copy.drop(columns='geometry').to_csv(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\건물_도로_시인성_분석_0509.csv',
    index=False,
    encoding='utf-8-sig'
)
