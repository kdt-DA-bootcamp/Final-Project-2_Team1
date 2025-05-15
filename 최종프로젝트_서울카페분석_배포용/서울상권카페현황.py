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
geo_path = r".\data\서울시_상권_경계_simplified.geojson"
summary_path = r".\data\상권별_카페요약.csv"
cafe_data_base_path = r".\data\상권별_카페데이터"

# ✅ 페이지 설정
st.set_page_config(layout="wide")
st.markdown("<h1 style='color: white;'>☕ 서울 상권 카페 현황</h1>", unsafe_allow_html=True)
st.markdown("#### 🗺️ 지도에서 상권을 클릭하거나 필터를 조정해보세요")

# ✅ 데이터 로딩
@st.cache_data
def load_data():
    gdf = gpd.read_file(geo_path)
    df_summary = pd.read_csv(summary_path)

    gdf["TRDAR_CD"] = gdf["TRDAR_CD"].astype(str).str.strip()
    df_summary["상권_코드"] = df_summary["상권_코드"].astype(str).str.strip()

    merged = gdf.merge(df_summary, left_on="TRDAR_CD", right_on="상권_코드", how="left")
    merged = merged[merged["상권_카페수"].fillna(0) > 0]
    merged["성공률"] = merged["성공률"].fillna(merged["성공률"].mean(skipna=True))
    return merged

gdf = load_data()

# # ✅ 필터 옵션 UI (사이드바로 이동)
# st.sidebar.header("📊 필터 조건")
# success_filter = st.sidebar.slider("성공률 (이상)", 0, 100, 0)
# cafe_count_filter = st.sidebar.slider("카페 수 (이상)", 0, 300, 0)

# ✅ 이 두 줄을 주석 처리된 슬라이더 아래에 추가
success_filter = st.session_state.get("현황_성공률", 0)
cafe_count_filter = st.session_state.get("현황_카페수", 0)

# ✅ 색상 매핑 정의 (YlOrRd 고정) → 전체 gdf 기준으로 고정된 범위 사용
min_val = gdf["성공률"].min()
max_val = gdf["성공률"].max()
if min_val == max_val:
    min_val -= 1
colormap = linear.YlOrRd_09.scale(min_val, max_val)
colormap.caption = "상권별 성공률 (%)"

# ✅ 필터 적용 후 새로운 gdf 생성
filtered_gdf = gdf[(gdf["성공률"] >= success_filter) & (gdf["상권_카페수"] >= cafe_count_filter)]

# ✅ 지도 생성 및 GeoJson 색상 매핑 적용
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11.5, tiles="CartoDB positron", control_scale=True)

# ✅ GeoJson 색상 매핑 직접 적용
if not filtered_gdf.empty:
    def get_color_style(feature):
        rate = feature["properties"].get("성공률", 0)
        return {
            "fillColor": colormap(rate),
            "color": "gray",
            "weight": 0.3,
            "fillOpacity": 0.7
        }

    GeoJson(
        filtered_gdf,
        style_function=get_color_style,
        tooltip=GeoJsonTooltip(
            fields=["상권명", "행정동", "성공률_표시", "인구_밀집도_표시", "카페_밀집도_표시"],
            aliases=["상권명", "행정동", "성공률", "인구 밀집도", "카페 밀집도"],
            localize=True,
            sticky=False,
            labels=True
        )
    ).add_to(m)

colormap.add_to(m)

# ✅ 지도 렌더링
output = st_folium(m, height=800, use_container_width=True)

# ✅ 하단 설명 (지도 아래 유지)
st.markdown("""
<small style='color:gray'>
※ 성공률은 해당 상권 내 카페들의 평점, 리뷰 수, 영업기간, 추정 매출 등을 바탕으로  
종합 점수를 계산한 뒤, **상위 30%를 '성공'으로 분류하여 계산한 비율입니다.**<BR>
※ 인구 밀집도와 카페 밀집도는 **상권 500m² 당 총 유동인구 수 / 등록된 카페 수** 기준으로 계산되었습니다.  
</small>
""", unsafe_allow_html=True)

# ✅ 클릭 시 해당 상권 정보 및 마커 표시
if output["last_clicked"]:
    clicked_point = Point(output["last_clicked"]["lng"], output["last_clicked"]["lat"])
    selected = filtered_gdf[filtered_gdf.geometry.contains(clicked_point)]

    if not selected.empty:
        code = selected.iloc[0]["TRDAR_CD"]
        name = selected.iloc[0]["상권명"]
        rate = selected.iloc[0]["성공률"]
        st.markdown(f"### 📍 선택된 상권: **{name}**")

        # ✅ 해당 상권 CSV 불러오기
        file_path = os.path.join(cafe_data_base_path, f"{code}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding="utf-8-sig")
            df.columns = df.columns.str.strip()
            if "위도" in df.columns and "경도" in df.columns:
                df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
                df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
                df = df.dropna(subset=["위도", "경도"])

                # ✅ 마커 지도 생성 (상권 경계 포함)
                m2 = folium.Map(location=[df["위도"].mean(), df["경도"].mean()], zoom_start=16, tiles="CartoDB positron")

                # 상권 경계 색상 표시
                GeoJson(
                    selected,
                    style_function=lambda x: {
                        "fillColor": colormap(rate),
                        "color": colormap(rate),
                        "weight": 2,
                        "fillOpacity": 0.5,
                    }
                ).add_to(m2)


                for _, row in df.iterrows():
                    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(row.get('도로명주소', ''))}"

                    popup = f"""
                    <b>{row.get('상호명','')}</b><br><br>

                    📦 운영기간: {row.get('운영기간_설명', '')} (점수: {row.get('period_score', 0):.1f})<br>
                    📈 추정 매출: {int(row.get('카페_추정매출', 0)):,}원 (점수: {row.get('sales_score_grouped', 0):.1f})<br>
                    🌟 평점: {row.get('별점', '')} (점수: {row.get('rating_score', 0):.1f})<br>
                    📝 리뷰 수: {row.get('리뷰수', '')} (점수: {row.get('5bin_review_score', 0):.1f})<br>
                    🚘 주차: {row.get('주차_가능', '')} (점수: {row.get('parking_score', 0):.1f})<br>
                    🏢 층수: {row.get('층수_정리', '')} (점수: {row.get('floor_score', 0):.1f})<br>
                    📊 총점: {row.get('총점', 0):.1f}<br>
                    <a href="{naver_url}" target="_blank" title="네이버지도로 이동">🗺️ 지도 열기</a>
                    """

                    tooltip = f"""
                    <b>{row.get('상호명', '')}</b><br>
                
                    """

                    Marker(
                        location=[row["위도"], row["경도"]],
                        tooltip=tooltip,  # ✅ 마우스 오버 시 정보 표시
                        popup=Popup(popup, max_width=350)  # ✅ 클릭 시 상세 정보 표시
                    ).add_to(m2)


                st_folium(m2, height=500, use_container_width=True)
                st.markdown(f"✅ 카페 수: **{len(df)}개**")
                # ✅ 정렬
                df_sorted = df.sort_values(by="총점", ascending=False)

                # ✅ 숨길 컬럼 정의
                cols_to_hide = [
                    "상가업소번호", "상권_코드", "상권_코드_명", "경도", "위도", "층정보",
                    "period_score", "rating_score", "5bin_review_score",
                    "sales_score_grouped", "profit_score_grouped",
                    "parking_score", "floor_score", "추정_순이익"
                ]

                # ✅ 표시할 컬럼만 남김
                visible_cols = [col for col in df_sorted.columns if col not in cols_to_hide]

                # ✅ '지점명' 다음에 '총점' 오도록 순서 재조정
                if "지점명" in visible_cols and "총점" in visible_cols:
                    visible_cols.remove("총점")  # 일단 제거
                    idx = visible_cols.index("지점명")
                    visible_cols.insert(idx + 1, "총점")  # '지점명' 다음에 삽입

                # ✅ 표시
                st.dataframe(df_sorted[visible_cols])
                
            else:
                st.warning("해당 CSV에 위도/경도 정보가 없습니다.")
        else:
            st.warning("해당 상권에 대한 상세 CSV 파일이 없습니다.")

# ✅ 전체 상권 요약 테이블
st.markdown("### 📋 상권 요약")
st.dataframe(
    filtered_gdf[["상권명", "행정동", "상권_카페수", "성공률", "인구_밀집도_표시", "카페_밀집도_표시"]]
    .sort_values(by="성공률", ascending=False).reset_index(drop=True)
)
