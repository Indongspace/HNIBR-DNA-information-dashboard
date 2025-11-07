# pages/3_천연물 추출물 소재 확보 현황.py
import pandas as pd
import streamlit as st
import altair as alt
from pathlib import Path

st.set_page_config(page_title="천연물 추출물 소재 확보 현황(국명·학명 집계)", layout="wide")
st.title("국립호남권생물자원관 천연물 추출물 소재 확보 현황 · 국명/학명 집계")

# -----------------------------
# 데이터 경로 (CSV 권장)
# -----------------------------
DEFAULT_DATA = "data/국립호남권생물자원관_섬생물소재은행_천연물 추출물 소재 확보 리스트_20241217.csv"
data_path = st.sidebar.text_input("데이터 파일 경로", DEFAULT_DATA)
st.sidebar.caption("국립호남권생물자원관이 보유하고 있는 천연물 추출물 소재 확보 리스트 데이터입니다.")

# 표시 옵션
label_font  = st.sidebar.slider("축 글자 크기", 9, 16, 11)
bar_size    = st.sidebar.slider("막대 두께(픽셀)", 10, 40, 20)
top_n       = st.sidebar.slider("Top-N 표시 개수", 5, 50, 20)
show_labels = st.sidebar.checkbox("막대 라벨 표시", True)
search_kw   = st.sidebar.text_input("이름/학명 포함 검색", "")

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
            raise ImportError("엑셀(.xlsx) 사용 시 `pip install openpyxl` 필요")
        return pd.read_excel(p, engine="openpyxl")
    else:
        raise ValueError("지원 형식: .csv, .xlsx")

try:
    df_raw = load_table(data_path)
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# -----------------------------
# 스키마 추론 (분류군/국명/학명)
# -----------------------------
cols_lower = {c: str(c).strip().lower() for c in df_raw.columns}

def find_col(keys):
    for c in df_raw.columns:
        low = cols_lower[c]
        if any(k in low for k in keys):
            return c
    return None

taxon_col   = find_col(["분류군", "taxon", "class", "군"])  # 텍스트 안내용
korean_col  = find_col(["국명", "한글명", "korean", "이름"])
sci_col     = find_col(["학명", "scientific", "species", "binomial"])

# 부족하면 선택 유도 (국명/학명은 필수)
missing = []
if korean_col is None: missing.append("국명")
if sci_col   is None: missing.append("학명")

if missing:
    st.warning("다음 컬럼을 자동탐지하지 못했습니다. 아래에서 직접 선택하세요.")
    col1, col2 = st.columns(2)
    with col1:
        korean_col = st.selectbox("국명 컬럼", df_raw.columns, index=0) if korean_col is None else korean_col
    with col2:
        sci_col    = st.selectbox("학명 컬럼", df_raw.columns, index=1) if sci_col is None else sci_col

# -----------------------------
# 전처리 (여기서 .str.strip() 사용!)
# -----------------------------
df = df_raw.copy()
cols_to_clean = [korean_col, sci_col] + ([taxon_col] if taxon_col else [])
for c in cols_to_clean:
    # 각 셀에 대해 문자열 변환 후 공백 제거
    df[c] = df[c].astype(str).str.strip()

# -----------------------------
# 분류군 안내(텍스트만)
# -----------------------------
if taxon_col:
    _tax = df_raw[taxon_col].astype(str).str.strip()
    unique_taxa = _tax.dropna().unique().tolist()
    if len(unique_taxa) == 1:
        one_taxon = unique_taxa[0]
        total_cnt = int((_tax == one_taxon).sum())
        st.info(f"※ 분류군: **{one_taxon}** · 보유 개수 **{total_cnt:,}**건")
    else:
        st.caption(f"분류군 고유값: {len(unique_taxa):,}개 (본 페이지는 국명·학명 중심 시각화)")

# -----------------------------
# 검색 필터 (국명/학명만 대상으로)
# -----------------------------
if search_kw:
    kw = str(search_kw).strip()
    mask = (
        df[korean_col].str.contains(kw, case=False, na=False) |
        df[sci_col].str.contains(kw, case=False, na=False)
    )
    df = df[mask]

# -----------------------------
# 집계 유틸
# -----------------------------
def count_by(col):
    s = df[col].replace({"nan": None, "None": None}).dropna()
    agg = s.value_counts().rename_axis(col).reset_index(name="건수")
    total = int(agg["건수"].sum()) if not agg.empty else 0
    agg["비율"] = 0 if total == 0 else agg["건수"] / total
    return agg, total

alt.themes.enable("none")
axis_y    = alt.Axis(title=None, labelFontSize=label_font)
axis_xcnt = alt.Axis(title="건수", labelFontSize=label_font)
axis_xpct = alt.Axis(title="비율", format="%", labelFontSize=label_font)

def bar_chart(df_cnt, name_col, value_col="건수", top=20, pct=False):
    # Top 정렬 및 순위 부여
    src = df_cnt.sort_values("비율" if pct else value_col, ascending=False).head(top).copy()
    src = src.reset_index(drop=True)
    src["rank"] = src.index + 1

    # ✅ Top 1~5 점진적 색상, 6위 이후 회색으로 미리 계산
    def rank_to_color(r: int) -> str:
        if r == 1: return "#004488"  # 가장 진하게
        if r == 2: return "#2E6EB5"
        if r == 3: return "#5B8BD5"
        if r == 4: return "#87A9E2"
        if r == 5: return "#B4C7EF"  # 가장 옅게
        return "#D9D9D9"            # 6위 이후 회색

    src["색상"] = src["rank"].apply(rank_to_color)

    enc_x = alt.X(("비율:Q" if pct else "건수:Q"),
                  axis=(axis_xpct if pct else axis_xcnt))

    bars = (
        alt.Chart(src)
        .mark_bar(size=bar_size)
        .encode(
            y=alt.Y(f"{name_col}:N", sort="-x", axis=axis_y),
            x=enc_x,
            # ✅ 계산된 색상값을 그대로 사용(스케일 없음)
            color=alt.Color("색상:N", legend=None, scale=None),
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
# 탭 구성: 국명/학명 + 국명×학명
# -----------------------------
tab1, tab2, tab3 = st.tabs(["국명 집계", "학명 집계", "국명×학명"])

with tab1:
    cnt_kor, tot_kor = count_by(korean_col)
    st.caption(f"(현재 필터 기준) 총 {tot_kor:,} 건 · 고유 국명 {cnt_kor.shape[0]:,}종")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("국명 Top-N (건수)")
        st.altair_chart(bar_chart(cnt_kor, korean_col, "건수", top=top_n, pct=False), use_container_width=True)
    with c2:
        st.subheader("국명 Top-N (비율)")
        st.altair_chart(bar_chart(cnt_kor, korean_col, "건수", top=top_n, pct=True), use_container_width=True)
    st.dataframe(cnt_kor.head(200), use_container_width=True)

with tab2:
    cnt_sci, tot_sci = count_by(sci_col)
    st.caption(f"(현재 필터 기준) 총 {tot_sci:,} 건 · 고유 학명 {cnt_sci.shape[0]:,}종")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("학명 Top-N (건수)")
        st.altair_chart(bar_chart(cnt_sci, sci_col, "건수", top=top_n, pct=False), use_container_width=True)
    with c2:
        st.subheader("학명 Top-N (비율)")
        st.altair_chart(bar_chart(cnt_sci, sci_col, "건수", top=top_n, pct=True), use_container_width=True)
    st.dataframe(cnt_sci.head(200), use_container_width=True)

with tab3:
    st.subheader("국명 × 학명 교차표 (Top-N 페어만)")
    top_pairs = st.slider("표시할 페어 Top-N", 5, 30, 50)

    # 1) 국명×학명 교차 집계
    cross = (
        df[[korean_col, sci_col]]
        .dropna()
        .groupby([korean_col, sci_col], as_index=False)
        .size()
        .rename(columns={"size": "건수"})
    )

    # 2) 건수 상위 N개 페어만 선택
    cross_top = cross.sort_values("건수", ascending=False).head(top_pairs)

    st.caption(f"(현재 필터 기준) 표시 페어: {len(cross_top):,} / 전체 페어: {len(cross):,}")

    if cross_top.empty:
        st.info("조건에 맞는 페어가 없습니다. Top-N을 늘려보세요.")
    else:
        # 3) 축 정렬(상위 N 내에서만 가중치 합 순)
        kor_order = (cross_top.groupby(korean_col, as_index=False)["건수"].sum()
                               .sort_values("건수", ascending=False)[korean_col].tolist())
        sci_order = (cross_top.groupby(sci_col, as_index=False)["건수"].sum()
                               .sort_values("건수", ascending=False)[sci_col].tolist())

        # 4) 히트맵
        heat = (
            alt.Chart(cross_top)
            .mark_rect()
            .encode(
                y=alt.Y(f"{korean_col}:N", sort=kor_order,
                        axis=alt.Axis(title=None, labelFontSize=label_font)),
                x=alt.X(f"{sci_col}:N", sort=sci_order,
                        axis=alt.Axis(title=None, labelAngle=-40, labelFontSize=label_font)),
                color=alt.Color("건수:Q", title="건수"),
                tooltip=[korean_col, sci_col, alt.Tooltip("건수:Q", format=",.0f")],
            )
            .properties(
                height=max(360, len(kor_order) * (bar_size // 2 + 4))
            )
            .configure_view(stroke=None)
            .configure_axis(labelOverlap=False, grid=True, gridOpacity=0.2)
        )

        st.altair_chart(heat, use_container_width=True)

        with st.expander("표(Top-N 페어) 보기"):
            st.dataframe(cross_top.sort_values("건수", ascending=False).reset_index(drop=True),
                         use_container_width=True)


# -----------------------------
# 데이터 미리보기
# -----------------------------
with st.expander("원본 데이터 미리보기 / 컬럼 확인"):
    if taxon_col:
        st.write("분류군 컬럼:", taxon_col)
    st.write("국명 컬럼:", korean_col)
    st.write("학명 컬럼:", sci_col)
    st.dataframe(df_raw.head(30), use_container_width=True)
