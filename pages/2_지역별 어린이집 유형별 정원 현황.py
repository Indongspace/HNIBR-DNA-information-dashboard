# pages/2_지역별 어린이집 유형별 정원 현황.py
import pandas as pd
import streamlit as st
import altair as alt
from pathlib import Path

st.set_page_config(page_title="지역별 어린이집 유형별 정원(개수·비율·합계)", layout="wide")
st.title("지역별 어린이집 유형별 정원 현황")

# -----------------------------
# 데이터 경로 입력 (CSV 권장)
# -----------------------------
DEFAULT_DATA = "data/지역별 어린이집 유형별 정원 현황.csv"
data_path = st.sidebar.text_input("데이터명: 지역별 어린이집 유형별 정원 현황", DEFAULT_DATA)
st.sidebar.caption("행정구역별, 어린이집 유형별 정원 현황입니다.")

# 표시 옵션
label_font          = st.sidebar.slider("축 글자 크기", 9, 16, 11)
bar_size            = st.sidebar.slider("막대 두께(픽셀)", 10, 40, 20)
show_total_labels   = st.sidebar.checkbox("총합 라벨 표시", True)
show_segment_labels = st.sidebar.checkbox("세부(유형) 라벨 표시", False)
segment_label_type  = st.sidebar.radio("세부 라벨 방식", ["개수", "비율(%)"], horizontal=True)

# -----------------------------
# 데이터 로더 (CSV 우선)
# -----------------------------
@st.cache_data
def load_table(path_str: str) -> pd.DataFrame:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {p}")
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p, encoding="utf-8-sig")
    elif p.suffix.lower() in (".xls", ".xlsx"):
        try:
            import openpyxl  # noqa
        except ImportError:
            raise ImportError("엑셀(.xlsx)을 쓰려면 openpyxl이 필요합니다. "
                              "CSV로 저장하거나 `pip install openpyxl` 후 다시 시도하세요.")
        return pd.read_excel(p, engine="openpyxl")
    else:
        raise ValueError("지원 형식: .csv, .xlsx")

try:
    df_raw = load_table(data_path)
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# -----------------------------
# 스키마 추론
# -----------------------------
region_candidates = [c for c in df_raw.columns
                     if any(k in str(c) for k in ["구분", "시도", "지역", "행정구역", "시·도", "시ㆍ도"])]
region_col = region_candidates[0] if region_candidates else df_raw.columns[0]

# (선택) 도시규모/그룹 컬럼 자동 탐지
group_candidates = [c for c in df_raw.columns
                    if any(k in str(c) for k in ["도시", "규모", "분류", "그룹"])
                    or set(map(str, df_raw[c].dropna().unique())) <= {"대도시", "중소도시", "농어촌"}]
group_col = group_candidates[0] if group_candidates else None

# 숫자 변환 (천단위 콤마 제거)
df = df_raw.copy()
for c in df.columns:
    if c not in [region_col, group_col]:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",", "").str.strip(),
            errors="coerce"
        )

# 유형 컬럼(‘계/합계’ 제외)
value_cols_all = [c for c in df.columns if c not in [region_col, group_col, "계", "합계", "__합계__"]]

# -----------------------------
# 필터 UI
# -----------------------------
if group_col:
    groups = ["전체"] + [g for g in df[group_col].dropna().unique().tolist()]
    chosen_group = st.radio("도시규모 그룹 필터", groups, horizontal=True)
    if chosen_group != "전체":
        df = df[df[group_col] == chosen_group]

chosen_types = st.multiselect("비교할 어린이집 유형 선택", value_cols_all, default=value_cols_all)
if not chosen_types:
    st.warning("최소 1개의 유형을 선택하세요.")
    st.stop()
value_cols = chosen_types

# -----------------------------
# 합계/비율 계산
# -----------------------------
# 시도별 총합(= '계' 있으면 사용, 없으면 유형 합산)
if "계" in df.columns:
    total_series = df.groupby(region_col)["계"].sum()
elif "합계" in df.columns:
    total_series = df.groupby(region_col)["합계"].sum()
else:
    total_series = df.groupby(region_col)[value_cols].sum().sum(axis=1)

# 롱포맷 + 시도합계/비율
df_long = (
    df.melt(id_vars=[region_col], value_vars=value_cols,
            var_name="유형", value_name="개수")
    .groupby([region_col, "유형"], as_index=False)["개수"].sum()
)
df_long["총합"] = df_long[region_col].map(total_series)
df_long = df_long[df_long["총합"] > 0]
df_long["비율"] = df_long["개수"] / df_long["총합"]

# 시도 정렬(총합 내림차순)
region_order = (
    df_long.groupby(region_col, as_index=False)["총합"].max()
           .sort_values("총합", ascending=False)[region_col]
           .tolist()
)

# -----------------------------
# 보기 모드
# -----------------------------
mode = st.radio(
    "보기",
    ["① 전체 시·도 비교(누적 막대: 총합 길이 + 유형 분할)", "② 특정 시·도 상세(유형별 % 가로 막대)"],
    horizontal=True
)

# Altair 공통 설정 (최후에만 적용)
alt.themes.enable("none")
axis_y    = alt.Axis(title=None, labelFontSize=label_font, labelLimit=400)
axis_xcnt = alt.Axis(title="어린이집 정원(총합 길이)", labelFontSize=label_font)
axis_xpct = alt.Axis(title="비율", format="%", labelFontSize=label_font)

# 동적 높이
n_region   = len(region_order)
auto_height = max(360, n_region * (bar_size + 6))

# -----------------------------
# ① 전체: 누적 막대(총합 길이 = ‘계’)
# -----------------------------
if mode.startswith("①"):
    base_bars = (
        alt.Chart(df_long)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y(f"{region_col}:N", sort=region_order, axis=axis_y),
            x=alt.X("sum(개수):Q", axis=axis_xcnt),
            color=alt.Color("유형:N", title="유형"),
            tooltip=[
                alt.Tooltip(f"{region_col}:N", title="시·도"),
                alt.Tooltip("유형:N"),
                alt.Tooltip("sum(개수):Q", title="유형별 정원", format=",.0f"),
                alt.Tooltip("sum(비율):Q", title="유형별 비율", format=".1%"),
                alt.Tooltip("max(총합):Q", title="총정원(명)", format=",.0f")
            ],
        )
        .properties(height=auto_height)
    )

    layers = [base_bars]

    # 세그먼트 라벨(개수 또는 비율) — 막대 내부/끝
    if show_segment_labels:
        seg_field = "sum(개수)" if segment_label_type == "개수" else "sum(비율)"
        seg_fmt   = ",.0f" if segment_label_type == "개수" else ".0%"
        seg_text = (
            alt.Chart(df_long)
            .mark_text(dx=3, baseline="middle", align="left", color="#333")
            .encode(
                y=alt.Y(f"{region_col}:N", sort=region_order, axis=None),
                x=alt.X("sum(개수):Q", stack="zero"),
                detail="유형:N",
                text=alt.Text(f"{seg_field}:Q", format=seg_fmt),
            )
        )
        layers.append(seg_text)

    # 총합(계) 라벨 — 막대 끝
    if show_total_labels:
        total_text = (
            alt.Chart(df_long)
            .mark_text(dx=6, baseline="middle", align="left", fontWeight="bold", color="#000")
            .encode(
                y=alt.Y(f"{region_col}:N", sort=region_order, axis=None),
                x=alt.X("sum(개수):Q"),
                text=alt.Text("max(총합):Q", format=",.0f"),
            )
        )
        layers.append(total_text)

    chart_all = alt.layer(*layers)
    # ✅ configure_* 는 레이어 합성 후 '최종 한 번만'
    chart_all = chart_all.configure_view(stroke=None).configure_axis(labelOverlap=False)
    st.altair_chart(chart_all, use_container_width=True)

# -----------------------------
# ② 단일 시·도 상세: 유형별 % 가로 막대
# -----------------------------
else:
    sel = st.selectbox("시·도 선택", region_order)
    sub = df_long[df_long[region_col] == sel].copy().sort_values("비율", ascending=False)

    bars = (
        alt.Chart(sub)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y("유형:N", sort="-x", axis=axis_y),
            x=alt.X("비율:Q", axis=axis_xpct),
            color=alt.Color("유형:N", legend=None),
            tooltip=[
                alt.Tooltip("유형:N"),
                alt.Tooltip("개수:Q", title="개수", format=",.0f"),
                alt.Tooltip("비율:Q", title="비율", format=".1%"),
                alt.Tooltip("max(총합):Q", title="총합(계)", format=",.0f"),
            ],
        )
        .properties(height=max(320, len(sub) * (bar_size + 6)))
    )

    layers2 = [bars]
    if show_segment_labels:
        label2 = (
            alt.Chart(sub)
            .mark_text(dx=3, align="left", baseline="middle", color="#333")
            .encode(
                y=alt.Y("유형:N", sort="-x", axis=None),
                x=alt.X("비율:Q"),
                text=alt.Text("비율:Q", format=".0%"),
            )
        )
        layers2.append(label2)

    chart_one = alt.layer(*layers2).configure_view(stroke=None).configure_axis(labelOverlap=False)

    st.subheader(f"【{sel}】 유형별 비율(%)")
    st.altair_chart(chart_one, use_container_width=True)

# -----------------------------
# 시·도별 합계 TOP10
# -----------------------------
st.subheader("시·도별 합계(계) TOP 10")
top10 = (
    df_long.groupby(region_col, as_index=False)[["총합"]].max()
           .sort_values("총합", ascending=False)
           .head(10)
           .rename(columns={"총합": "총정원(명)"})
)
st.dataframe(top10, use_container_width=True)

# -----------------------------
# 데이터 미리보기
# -----------------------------
with st.expander("데이터 미리보기 / 컬럼 확인"):
    st.write("지역(시도) 컬럼:", region_col)
    if group_col:
        st.write("도시규모 그룹 컬럼:", group_col, " (예시:", ", ".join(map(str, df_raw[group_col].dropna().unique()[:5])), ")")
    st.dataframe(df_raw.head(20), use_container_width=True)
