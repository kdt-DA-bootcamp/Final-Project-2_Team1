import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium import GeoJson, GeoJsonTooltip, Marker, Popup
from shapely.geometry import Point
from streamlit_folium import st_folium
import os
from branca.colormap import linear
import urllib.parse

# ✅ 경로 설정
boundary_path = "./data/서울시_상권_경계_simplified.geojson"
success_path = "./data/매물_성공확률.csv"
summary_path = "./data/상권별_매물요약.csv"

# ✅ 페이지 설정
st.set_page_config(layout="wide")
st.markdown("<h1 style='color: white;'>📌 서울 카페 매물 추천</h1>", unsafe_allow_html=True)
st.markdown("#### 🗺️ 지도에서 상권을 클릭하거나 필터를 조정해보세요")

# ✅ 데이터 로딩
def load_mamul_data():  # 고유한 함수명으로
    gdf = gpd.read_file(boundary_path)
    df_success = pd.read_csv(success_path)
    df_summary = pd.read_csv(summary_path)
    gdf["TRDAR_CD"] = gdf["TRDAR_CD"].astype(str)
    df_success["상권_코드"] = df_success["상권_코드"].astype(str)
    df_summary["상권_코드"] = df_summary["상권_코드"].astype(str)
    gdf = gdf.merge(df_summary, left_on="TRDAR_CD", right_on="상권_코드", how="left")
    gdf["성공률"] = gdf["성공률"].fillna(0)
    return gdf.set_index("TRDAR_CD"), df_success, df_summary

gdf_boundary, df_success, df_summary = load_mamul_data()

# # ✅ 사이드바 필터
# st.sidebar.header("📊 필터 조건")
# rent_range = st.sidebar.slider("월세 (만원 단위)", 0, 10000, (0, 1000))
# deal_range = st.sidebar.slider("보증금 (만원 단위)", 0, 1000000, (0, 300000))
# area_range = st.sidebar.slider("전용면적 (㎡)", 0, 1500, (0, 500))
# success_range_percent = st.sidebar.slider("성공률 (%)", 0, 100, (0, 100))
# success_range = (success_range_percent[0] / 100, success_range_percent[1] / 100)

# 🔁 통합시스템.py에서 정의한 필터값 불러오기
rent_range = st.session_state.get("추천_월세", (0, 1000))
deal_range = st.session_state.get("추천_보증금", (0, 300000))
area_range = st.session_state.get("추천_면적", (0, 500))
success_range_percent = st.session_state.get("추천_성공률", (0, 100))
success_range = (success_range_percent[0] / 100, success_range_percent[1] / 100)

# ✅ 상권 요약 기반 필터링
filtered_codes = df_summary[
    (df_summary["최대_월세"].between(*rent_range)) &
    (df_summary["최대_보증금"].between(*deal_range)) &
    (df_summary["최대_면적"].between(*area_range)) &
    (df_summary["평균_성공확률"].between(*success_range))
]["상권_코드"].unique()

gdf_filtered = gdf_boundary[gdf_boundary.index.isin(filtered_codes)]

# ✅ 색상 매핑 정의 (YlOrRd 고정)
min_val = gdf_boundary["성공률"].min()
max_val = gdf_boundary["성공률"].max()
if min_val == max_val:
    min_val -= 1
colormap = linear.YlOrRd_09.scale(min_val, max_val)
colormap.caption = "상권별 성공률 (%)"

# ✅ 지도 생성 및 GeoJson 색상 매핑 적용
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11.5, tiles="CartoDB positron", control_scale=True)

if not gdf_filtered.empty:
    def get_color_style(feature):
        rate = feature["properties"].get("성공률", 0)
        return {
            "fillColor": colormap(rate),
            "color": "gray",
            "weight": 0.3,
            "fillOpacity": 0.7
        }

    GeoJson(
        gdf_filtered.reset_index(),
        style_function=get_color_style,
        tooltip=GeoJsonTooltip(
            fields=["TRDAR_CD_N", "행정동", "성공률_표시"],
            aliases=["상권명", "행정동", "성공률"],
            localize=True,
            sticky=False,
            labels=True
        )
    ).add_to(m)

colormap.add_to(m)
output = st_folium(m, height=800, use_container_width=True)

# ✅ 여기부터 추가
st.markdown("""
<small style='color:gray'>
※ 성공률 60% 이상 : 검토해 볼 만한 입지
</small>
""", unsafe_allow_html=True)

# ✅ 상권 클릭 시 매물 필터링
if output["last_clicked"]:
    point = Point(output["last_clicked"]["lng"], output["last_clicked"]["lat"])
    selected = gdf_boundary[gdf_boundary.geometry.contains(point)]

    if not selected.empty:
        code = selected.index[0]
        name = selected.iloc[0]["TRDAR_CD_N"]
        st.markdown(f"### 📍 선택된 상권: **{name}**")

        df_zone = df_success[df_success["상권_코드"] == code].copy()
        df_zone = df_zone[(df_zone["rentPrc"].between(*rent_range)) &
                          (df_zone["dealOrWarrantPrc"].between(*deal_range)) &
                          (df_zone["area2"].between(*area_range)) &
                          (df_zone["성공확률"].between(*success_range))]

        if not df_zone.empty:
            m2 = folium.Map(location=[df_zone["latitude"].mean(), df_zone["longitude"].mean()], zoom_start=16, tiles="CartoDB positron")

            for _, row in df_zone.iterrows():
                popup = f"""
                <b>{row['articleName']}</b><br><br>
                ⭐ 성공확률: <b>{row['성공확률']*100:.1f}%</b><br>
                💰 보증금: {row['dealOrWarrantPrc']} / 월세: {row['rentPrc']}<br>
                📐 면적: {row['area2']}㎡<br>
                📍 층수: {row['층정보']}<br>
                🔗 <a href='https://new.land.naver.com/offices?articleNo={int(row['articleNo'])}' target='_blank'>네이버 매물 보기</a>
                """
                Marker(
                    location=[row["latitude"], row["longitude"]],
                    popup=Popup(popup, max_width=350),
                    icon=folium.Icon(color="green" if row["성공확률"] >= 0.8 else "blue", icon="info-sign")
                ).add_to(m2)

            GeoJson(
    selected,
    style_function=lambda x: {
        "fillColor": colormap(selected.iloc[0]["성공률"]),
        "color": colormap(selected.iloc[0]["성공률"]),
        "weight": 2,
        "fillOpacity": 0.4,
    }
).add_to(m2)

            st_folium(m2, height=500, use_container_width=True)

            
            preview_cols = [
                "articleName", "성공확률", "tradeTypeName", "rentPrc", "dealOrWarrantPrc",
                "area2", "floorInfo", "direction", "articleConfirmYmd",
                "지하철역_거리(m)", "버스정류장_거리(m)", "반경500m내_카페수", "est_총_유동인구_수_log"
            ]
            col_name_map = {
                "articleName": "매물명",
                "성공확률": "성공확률(%)",
                "tradeTypeName": "거래유형",
                "rentPrc": "월세(만원)",
                "dealOrWarrantPrc": "보증금/매매가(만원)",
                "area2": "전용면적(㎡)",
                "floorInfo": "층정보",
                "direction": "방향",
                "articleConfirmYmd": "확인일",
                "지하철역_거리(m)": "지하철역 거리(m)",
                "버스정류장_거리(m)": "버스정류장 거리(m)",
                "반경500m내_카페수": "500m내 카페 수",
                "est_총_유동인구_수_log": "유동인구 추정치 (로그)"
                
            }

            df_display = df_zone[preview_cols].copy()
            st.markdown(f"✅ 매물 수: **{len(df_display)}개**")

            df_display = df_display.sort_values("성공확률", ascending=False).reset_index(drop=True)
            df_display = df_display.rename(columns=col_name_map)
            st.dataframe(df_display)

        else:
            st.info("해당 상권에는 조건을 만족하는 매물이 없습니다.")
