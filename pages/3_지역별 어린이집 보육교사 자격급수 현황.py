# pages/3_지역별 어린이집 보육교사 자격급수 현황.py
import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="지역별 보육교사 자격급수 현황 (Long)", layout="wide")
st.title("지역별 어린이집 보육교사 자격급수 현황")

# -----------------------------
# 데이터 경로 (롱 포맷 CSV 권장: 시도, 자격급수, 유형, 개수)
# -----------------------------
DEFAULT_PATH = "data/지역별_보육교사_자격급수_long.csv"
data_path = st.sidebar.text_input("데이터명: 지역별 보육교사 자격증 현황입니다.", DEFAULT_PATH)
st.sidebar.caption("행정구역별, 보육교사 자격증 급수별 집계 현황입니다.")

bar_size   = st.sidebar.slider("막대 두께(px)", 10, 40, 18)
label_font = st.sidebar.slider("축 글자 크기", 9, 16, 11)
normalize  = st.sidebar.checkbox("비율(%)로 보기", value=False)
facet_cols = st.sidebar.slider("유형 패싯 열 수", 1, 4, 3)

# -----------------------------
# 로더
# -----------------------------
@st.cache_data
def load_table(path_str: str) -> pd.DataFrame:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {p}")
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p, encoding="utf-8-sig")
    elif p.suffix.lower() in (".xls", ".xlsx"):
        try:
            import openpyxl  # noqa
        except ImportError:
            raise ImportError("엑셀(.xlsx)을 읽으려면 openpyxl이 필요합니다. CSV로 저장하거나 openpyxl 설치 후 시도하세요.")
        df = pd.read_excel(p, engine="openpyxl")
    else:
        raise ValueError("CSV 또는 XLSX만 지원합니다.")
    return df

try:
    df = load_table(data_path)
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# -----------------------------
# 스키마 검증 & 정리
# -----------------------------
required = {"시도", "자격급수", "유형", "개수"}
missing = required - set(df.columns)
if missing:
    st.error(f"필수 열이 없습니다: {', '.join(missing)}")
    st.stop()

df["개수"] = pd.to_numeric(df["개수"], errors="coerce").fillna(0)
df["유형"] = (
    df["유형"].astype(str)
    .str.replace("•", "·", regex=False)
    .str.replace("  ", " ", regex=False)
    .str.strip()
)
df["자격급수"] = df["자격급수"].astype(str).str.strip()

# -----------------------------
# 필터
# -----------------------------
grades_all = [g for g in ["1급", "2급", "3급"] if g in df["자격급수"].unique().tolist()]
types_all  = sorted(df["유형"].dropna().unique().tolist())

sel_grades = st.multiselect("자격급수 선택", grades_all, default=grades_all)
sel_types  = st.multiselect("어린이집 유형 선택", types_all, default=types_all)

if not sel_grades or not sel_types:
    st.warning("자격급수와 유형을 최소 1개 이상 선택하세요.")
    st.stop()

fdf = df[df["자격급수"].isin(sel_grades) & df["유형"].isin(sel_types)].copy()

# -----------------------------
# 집계 & 보조 필드
# -----------------------------
agg = fdf.groupby(["시도", "유형", "자격급수"], as_index=False)["개수"].sum()
# 비율은 '시도' 총합 기준 (현재 선택 반영)
agg["시도총합"] = agg.groupby("시도")["개수"].transform("sum")
agg["비율"] = agg["개수"] / agg["시도총합"]

metric_field = "비율" if normalize else "개수"
metric_axis  = alt.Axis(title="비율" if normalize else "개수",
                        format="%" if normalize else ",.0f",
                        labelFontSize=label_font)

region_order = (
    agg.groupby("시도")["개수"].sum()
       .sort_values(ascending=False).index.tolist()
)

# -----------------------------
# 보기 모드
# -----------------------------
mode = st.radio("보기", ["① 전체(유형 합침, 급수 스택)", "② 유형별 패싯(급수 스택)"], horizontal=True)

alt.themes.enable("none")
axis_y = alt.Axis(title=None, labelFontSize=label_font, labelLimit=400)
auto_h = max(320, len(region_order) * (bar_size + 6))

if mode.startswith("①"):
    agg_total = (
        agg.groupby(["시도", "자격급수"], as_index=False)[["개수", "비율"]].sum()
    )
    chart = (
        alt.Chart(agg_total)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y("시도:N", sort=region_order, axis=axis_y),
            x=alt.X(f"sum({metric_field}):Q",
                    stack="normalize" if normalize else "zero",
                    axis=metric_axis),
            color=alt.Color("자격급수:N", title="자격급수", sort=["1급","2급","3급"]),
            tooltip=[
                alt.Tooltip("시도:N"),
                alt.Tooltip("자격급수:N"),
                alt.Tooltip("sum(개수):Q", title="개수", format=",.0f"),
                alt.Tooltip("sum(비율):Q", title="비율", format=".1%"),
            ],
        )
        .properties(height=auto_h)
    )
else:
    base = (
        alt.Chart(agg)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y("시도:N", sort=region_order, axis=axis_y),
            x=alt.X(f"sum({metric_field}):Q",
                    stack="normalize" if normalize else "zero",
                    axis=metric_axis),
            color=alt.Color("자격급수:N", title="자격급수", sort=["1급","2급","3급"]),
            tooltip=[
                alt.Tooltip("시도:N"),
                alt.Tooltip("유형:N"),
                alt.Tooltip("자격급수:N"),
                alt.Tooltip("sum(개수):Q", title="개수", format=",.0f"),
                alt.Tooltip("sum(비율):Q", title="비율", format=".1%"),
            ],
        )
        .properties(height=auto_h)
    )
    chart = base.facet(
        facet=alt.Facet("유형:N", title="어린이집 유형"),
        columns=facet_cols
    )

# Altair config는 최종 1회만 적용
chart = chart.configure_view(stroke=None).configure_axis(labelOverlap=False)
st.altair_chart(chart, use_container_width=True)

# # -----------------------------
# # 다운로드 (집계 데이터만 제공) — 원본 다운로드 제거됨
# # -----------------------------
# st.download_button(
#     "⬇️ 집계 데이터(현재 화면 기준) CSV",
#     data=agg.to_csv(index=False, encoding="utf-8-sig"),
#     file_name="자격급수_집계.csv",
#     mime="text/csv",
# )

# -----------------------------
# 시도별 합계 TOP10 (급수별 탭)
# -----------------------------
st.subheader("시도별 합계 TOP 10 (급수별)")

tabs = st.tabs([g for g in ["1급","2급","3급"] if g in sel_grades])

for i, g in enumerate([x for x in ["1급","2급","3급"] if x in sel_grades]):
    with tabs[i]:
        gdf = (agg[agg["자격급수"] == g]
               .groupby("시도", as_index=False)["개수"].sum()
               .sort_values("개수", ascending=False)
               .head(10)
               .rename(columns={"개수": "총합"}))
        # 표
        st.dataframe(gdf, use_container_width=True)
        # (선택) 간단한 막대 시각화
        bar = (
            alt.Chart(gdf)
            .mark_bar()
            .encode(
                y=alt.Y("시도:N", sort="-x", title=None),
                x=alt.X("총합:Q", title="총합", axis=alt.Axis(format=",.0f")),
                tooltip=[alt.Tooltip("시도:N"), alt.Tooltip("총합:Q", format=",.0f")]
            )
            .properties(height=max(300, len(gdf)*24))
            .configure_view(stroke=None)
        )
        st.altair_chart(bar, use_container_width=True)

# -----------------------------
# 데이터 미리보기
# -----------------------------
with st.expander("데이터 미리보기 / 컬럼 확인"):
    st.write("필수 컬럼 존재 여부:", required <= set(df.columns))
    st.dataframe(df.head(20), use_container_width=True)
