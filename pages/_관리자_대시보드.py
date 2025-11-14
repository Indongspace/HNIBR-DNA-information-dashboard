# pages/__관리자_대시보드.py
import streamlit as st
import pandas as pd
import altair as alt
from analytics import load_logs

st.set_page_config(page_title="관리자 대시보드", layout="wide")

st.title("관리자 대시보드")

# 1) 비밀번호 체크
ADMIN_PASSWORD = "hnibr1234" 

pwd = st.text_input("관리자 비밀번호", type="password")
if pwd != ADMIN_PASSWORD:
    st.info("관리자 비밀번호를 입력하세요.")
    st.stop()

st.success("관리자 모드 접속 완료 ✅")

# 2) 로그 불러오기
df = load_logs()

if df.empty:
    st.warning("아직 방문 로그가 없습니다.")
    st.stop()

# 날짜 필터
date_min = df["date"].min()
date_max = df["date"].max()
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("시작일", value=pd.to_datetime(date_min))
with col2:
    end_date = st.date_input("종료일", value=pd.to_datetime(date_max))

mask = (pd.to_datetime(df["date"]) >= pd.to_datetime(start_date)) & (
    pd.to_datetime(df["date"]) <= pd.to_datetime(end_date)
)
df_filtered = df[mask]

st.write(f"선택 기간 방문 로그 수: {len(df_filtered)}건")

# 일자별 방문자
st.subheader("일자별 방문자 수 (세션 기준)")
daily = (
    df_filtered.groupby("date")["session_id"]
    .nunique()
    .reset_index(name="visitors")
)

chart_daily = (
    alt.Chart(daily)
    .mark_line(point=True)
    .encode(
        x="date:T",
        y="visitors:Q",
        tooltip=["date:T", "visitors:Q"],
    )
)
st.altair_chart(chart_daily, use_container_width=True)

# 페이지별 조회수
st.subheader("페이지별 조회수")
page_counts = (
    df_filtered.groupby("page")["id"].count().reset_index(name="views")
    .sort_values("views", ascending=False)
)
st.table(page_counts)

# 원시 로그
with st.expander("원시 로그 데이터 보기"):
    st.dataframe(
        df_filtered.sort_values("timestamp", ascending=False),
        use_container_width=True,
    )
