import streamlit as st
from pathlib import Path

# ✅ 페이지 설정
st.set_page_config(layout="wide")

# ✅ session_state 초기화
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "추천"  # 매물 추천을 기본 탭으로

# ✅ 탭 구성 (순서 바꿈)
탭_추천, 탭_현황 = st.tabs(["📌 서울 카페 매물 추천", "☕ 서울 상권 카페 현황"])

# ✅ 사이드바 필터 정의
st.sidebar.header("📊 필터 조건")

# 🔼 상단: 매물 추천 필터
with st.sidebar.expander("📌 매물 추천 필터", expanded=(st.session_state.active_tab == "추천")):
    st.slider("월세 (만원)", 0, 10000, (0, 1000), key="추천_월세")
    st.slider("보증금/매매가 (만원)", 0, 1000000, (0, 300000), key="추천_보증금")
    st.slider("전용면적 (㎡)", 0, 1500, (0, 500), key="추천_면적")
    st.slider("성공률 (%)", 0, 100, (0, 100), key="추천_성공률")

# 🔽 하단: 카페 현황 필터
with st.sidebar.expander("☕ 카페 현황 필터", expanded=False):
    st.slider("성공률 (이상)", 0, 100, 0, key="현황_성공률")
    st.slider("카페 수 (개 이상)", 0, 300, 0, key="현황_카페수")

# ✅ 탭 1: 서울 카페 매물 추천
with 탭_추천:
    st.session_state.active_tab = "추천"
    추천_경로 = Path(r"C:/Users/hunae/Desktop/bootcamp/TIL/최종프로젝트2차/시각화/네이버부동산 매물 현황/3. 서울시_상가_분석데이터/서울카페매물추천.py")
    코드 = 추천_경로.read_text(encoding="utf-8").replace("st.set_page_config(layout=\"wide\")", "")
    exec(코드, globals())

# ✅ 탭 2: 서울 상권 카페 현황
with 탭_현황:
    st.session_state.active_tab = "현황"
    현황_경로 = Path(r"C:/Users/hunae/Desktop/bootcamp/TIL/최종프로젝트2차/시각화/서울 카페 현황/서울상권카페현황.py")
    코드 = 현황_경로.read_text(encoding="utf-8").replace("st.set_page_config(layout=\"wide\")", "")
    exec(코드, globals())
