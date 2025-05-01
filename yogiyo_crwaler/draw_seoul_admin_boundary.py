import os
import folium
import geopandas as gpd

# ✅ 파일 경로 설정
shp_path = "C:/Users/hunae/Desktop/bootcamp/TIL/최종프로젝트2차/요기요/LARD_ADM_SECT_SGG_서울/LARD_ADM_SECT_SGG_11_202504.shp"
csv_dir = r"C:\Users\hunae\Desktop\bootcamp\TIL\최종프로젝트2차\요기요\my_yogiyo\카페디저트_좌표별데이터_전체컬럼(0.01버전)"
step = 0.01

# ✅ 서울 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="cartodbpositron")

# ✅ 서울 행정경계 GeoDataFrame 로드
gdf = gpd.read_file(shp_path, encoding="cp949")
gdf = gdf.to_crs(epsg=4326)

# ✅ 서울 경계 시각화
folium.GeoJson(
    gdf.geometry,
    name="서울 행정경계",
    style_function=lambda x: {
        'fillColor': 'orange',
        'color': 'red',
        'weight': 2,
        'fillOpacity': 0.1
    }
).add_to(m)

# ✅ 격자 파일 기반 사각형 시각화
for fname in os.listdir(csv_dir):
    if fname.endswith(".csv"):
        try:
            lat_str, lng_str = fname.replace(".csv", "").split("_")
            lat = float(lat_str)
            lng = float(lng_str)
            bounds = [
                [lat, lng],
                [lat, lng + step],
                [lat + step, lng + step],
                [lat + step, lng]
            ]
            folium.Polygon(
                locations=bounds,
                color="blue",
                weight=1,
                fill=True,
                fill_opacity=0.1
            ).add_to(m)
        except Exception as e:
            print(f"⚠️ 오류 파일: {fname} → {e}")

# ✅ 저장
output_file = "서울_행정경계_격자지도.html"
m.save(output_file)
print(f"✅ 저장 완료: {output_file}")
