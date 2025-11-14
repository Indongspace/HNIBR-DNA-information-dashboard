# pages/1_국명_학명_집계.py
import pandas as pd
import streamlit as st
import altair as alt
from pathlib import Path
from analytics import log_visit

st.set_page_config(page_title="배양체 균류 소재 확보 현황(국명·학명 집계)", layout="wide")
log_visit("배양체 균류 소재 확보 현황(국명·학명 집계)")

st.title("국립호남권생물자원관 배양체 균류 소재 확보 현황 · 국명/학명 집계")

# -----------------------------
# 데이터 경로 입력 (CSV 권장)
# -----------------------------
DEFAULT_DATA = "data/국립호남권생물자원관_섬생물소재은행_ 배양체 균류 소재 확보 리스트_20241217.csv"
data_path = st.sidebar.text_input("데이터 파일 경로", DEFAULT_DATA)
st.sidebar.caption("국립호남권생물자원관이 보유하고 있는 배양체 균류 소재 확보 리스트 데이터입니다.")

# 표시 옵션
label_font = st.sidebar.slider("축 글자 크기", 9, 16, 11)
bar_size   = st.sidebar.slider("막대 두께(픽셀)", 10, 40, 20)
top_n      = st.sidebar.slider("표시 개수(상위)", 5, 50, 20)
show_labels = st.sidebar.checkbox("막대 라벨 표시", True)
search_kw   = st.sidebar.text_input("이름 필터(포함 검색)", "")

# -----------------------------
# 데이터 로더
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
            import openpyxl  # noqa: F401
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
# 스키마 추론: 국명/학명 컬럼 찾기
# -----------------------------
columns_lower = {c: str(c).strip().lower() for c in df_raw.columns}

def find_col(candidates):
    for c in df_raw.columns:
        low = columns_lower[c]
        if any(key in low for key in candidates):
            return c
    return None

# 국명 후보 예: 국명, 한글명, 종명(국명), 이름 등
korean_name_col = find_col(["국명", "한글명", "국 명", "korean", "국가명"]) or "국명"
# 학명 후보 예: 학명, scientific name, species 등
scientific_name_col = find_col(["학명", "scientific", "species", "binomial"]) or "학명"

missing_cols = [c for c in [korean_name_col, scientific_name_col] if c not in df_raw.columns]
if missing_cols:
    st.warning(f"컬럼 자동탐지 결과, 다음 컬럼을 찾지 못했습니다: {', '.join(missing_cols)}\n"
               f"→ 실제 컬럼명을 선택하세요.")
    col1, col2 = st.columns(2)
    with col1:
        korean_name_col = st.selectbox("국명 컬럼 선택", df_raw.columns, index=0)
    with col2:
        scientific_name_col = st.selectbox("학명 컬럼 선택", df_raw.columns, index=min(1, len(df_raw.columns)-1))

# 전처리: 문자열 통일(양끝 공백 제거)
df = df_raw.copy()
for c in [korean_name_col, scientific_name_col]:
    df[c] = df[c].astype(str).str.strip()

# 검색 필터 적용(국명/학명 모두에 부분일치)
if search_kw:
    kw = str(search_kw).strip()
    mask = df[korean_name_col].str.contains(kw, case=False, na=False) | df[scientific_name_col].str.contains(kw, case=False, na=False)
    df = df[mask]

# -----------------------------
# 집계 함수
# -----------------------------
def count_by(col):
    s = (df[col]
         .replace({"nan": None, "None": None})
         .dropna())
    agg = (s.value_counts()
             .rename_axis(col)
             .reset_index(name="건수"))
    total = int(agg["건수"].sum()) if not agg.empty else 0
    if total > 0:
        agg["비율"] = agg["건수"] / total
    else:
        agg["비율"] = 0.0
    return agg, total

# -----------------------------
# 차트 공통 설정
# -----------------------------
alt.themes.enable("none")
axis_y    = alt.Axis(title=None, labelFontSize=label_font)
axis_xcnt = alt.Axis(title="건수", labelFontSize=label_font)
axis_xpct = alt.Axis(title="비율", format="%", labelFontSize=label_font)

def bar_chart(df_cnt, name_col, value_col="건수", top=20, pct=False):
    # Top 정렬 및 순위 부여
    src = df_cnt.sort_values("비율" if pct else value_col, ascending=False).head(top).copy()
    src = src.reset_index(drop=True)
    src["rank"] = src.index + 1

    # Top 1~5 단계색, 6위 이후 회색
    def rank_to_color(r: int) -> str:
        if r == 1: return "#004488"   # 가장 진한 파랑
        if r == 2: return "#2E6EB5"
        if r == 3: return "#5B8BD5"
        if r == 4: return "#87A9E2"
        if r == 5: return "#B4C7EF"   # 가장 옅은 파랑
        return "#D9D9D9"              # 6위 이후 회색

    src["색상"] = src["rank"].apply(rank_to_color)

    enc_x = alt.X(("비율:Q" if pct else "건수:Q"),
                  axis=(axis_xpct if pct else axis_xcnt))

    bars = (
        alt.Chart(src)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y(f"{name_col}:N", sort="-x", axis=axis_y),
            x=enc_x,
            color=alt.Color("색상:N", legend=None, scale=None),  # 계산된 색상 직접 사용
            tooltip=[
                alt.Tooltip(f"{name_col}:N", title="이름"),
                alt.Tooltip("건수:Q", format=",.0f"),
                alt.Tooltip("비율:Q", format=".1%"),
                alt.Tooltip("rank:Q", title="순위"),
            ],
        )
        .properties(height=max(320, len(src) * (bar_size + 6)))
    )

    if show_labels:
        texts = (
            alt.Chart(src)
            .mark_text(dx=3, align="left", baseline="middle", color="#222")
            .encode(
                y=alt.Y(f"{name_col}:N", sort="-x", axis=None),
                x=enc_x,
                text=alt.Text(("비율:Q" if pct else "건수:Q"),
                              format=(".0%" if pct else ",.0f")),
            )
        )
        return (bars + texts).configure_view(stroke=None).configure_axis(labelOverlap=False)

    return bars.configure_view(stroke=None).configure_axis(labelOverlap=False)


# -----------------------------
# 레이아웃: 탭 3개
# -----------------------------
tab1, tab2, tab3 = st.tabs(["국명 집계", "학명 집계", "국명×학명 매트릭스"])

with tab1:
    cnt_kor, total_kor = count_by(korean_name_col)
    st.caption(f"총 {total_kor:,} 건 · 고유 국명 {cnt_kor.shape[0]:,} 종")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("국명 Top-N (건수)")
        st.altair_chart(bar_chart(cnt_kor, korean_name_col, "건수", top=top_n, pct=False), use_container_width=True)
    with c2:
        st.subheader("국명 Top-N (비율)")
        st.altair_chart(bar_chart(cnt_kor, korean_name_col, "건수", top=top_n, pct=True), use_container_width=True)
    st.dataframe(cnt_kor.head(200), use_container_width=True)

with tab2:
    cnt_sci, total_sci = count_by(scientific_name_col)
    st.caption(f"총 {total_sci:,} 건 · 고유 학명 {cnt_sci.shape[0]:,} 종")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("학명 Top-N (건수)")
        st.altair_chart(bar_chart(cnt_sci, scientific_name_col, "건수", top=top_n, pct=False), use_container_width=True)
    with c2:
        st.subheader("학명 Top-N (비율)")
        st.altair_chart(bar_chart(cnt_sci, scientific_name_col, "건수", top=top_n, pct=True), use_container_width=True)
    st.dataframe(cnt_sci.head(200), use_container_width=True)

with tab3:
    st.subheader("국명 × 학명 동시 분포(교차표)")
    cross = (df[[korean_name_col, scientific_name_col]]
                .dropna()
                .groupby([korean_name_col, scientific_name_col], as_index=False)
                .size()
                .rename(columns={"size": "건수"}))
    st.caption(f"페어(국명-학명) {cross.shape[0]:,} 조합")
    # 상위 조합만 표시할 수 있도록 제한
    cross_top = cross.sort_values("건수", ascending=False).head(top_n * 5)

    heat = (
        alt.Chart(cross_top)
        .mark_rect()
        .encode(
            y=alt.Y(f"{korean_name_col}:N", sort="-x", axis=axis_y),
            x=alt.X(f"{scientific_name_col}:N", axis=alt.Axis(labelAngle=-40, labelFontSize=label_font)),
            color=alt.Color("건수:Q", title="건수"),
            tooltip=[korean_name_col, scientific_name_col, alt.Tooltip("건수:Q", format=",.0f")],
        )
        .properties(height=max(360, len(cross_top[korean_name_col].unique()) * (bar_size // 2 + 4)))
    )
    st.altair_chart(heat.configure_view(stroke=None), use_container_width=True)
    with st.expander("교차표(상위 일부) 미리보기"):
        st.dataframe(cross_top, use_container_width=True)

# -----------------------------
# 데이터 미리보기
# -----------------------------
with st.expander("원본 데이터 미리보기 / 컬럼 확인"):
    st.write("국명 컬럼:", korean_name_col)
    st.write("학명 컬럼:", scientific_name_col)
    st.dataframe(df_raw.head(30), use_container_width=True)
