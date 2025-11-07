import streamlit as st

st.set_page_config(page_title="DNA의 정원: 생명의 코드 수집기록", page_icon="📰", layout="wide")

# ─────────────────────────────
# 헤더
# ─────────────────────────────
import base64
from pathlib import Path

# 배경 이미지 파일 경로
hero_image = Path("images/79766004-dna-research-with-a-sample-hand-with-a-test-tube-on-a-dna-background.jpg")

# base64 인코딩
if hero_image.exists():
    encoded = base64.b64encode(hero_image.read_bytes()).decode()
    hero_data_uri = f"data:image/jpeg;base64,{encoded}"
else:
    hero_data_uri = None

# 히어로 섹션 렌더링
if hero_data_uri:
    st.markdown(
        f"""
        <div style="
            background-image: url('{hero_data_uri}');
            background-size: cover;
            background-position: center;
            width: 100%;
            height: 380px;
            border-radius: 12px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
            font-weight: 600;
            font-size: 2.3rem;
            text-shadow: 0 2px 8px rgba(0,0,0,0.55);
        ">
            DNA의 정원: 생명의 코드 수집기록
        </div>
        """,
        unsafe_allow_html=True
    )

st.title('DNA의 정원: 생명의 코드 수집기록')

st.write("""
\n\n
국립호남권생물자원관에서는 섬생물소재은행이 보유 중인 **배양체 균류**, **유전자원 DNA**, **천연물 추출물**의 보유 현황을 수집·정리하고 있습니다.\n  
이 데이터들은 공공 연구 데이터를 **바이오산업·식품·화장품·의약·생명정보(AAI) 분야**에서 활용하기 위한 **원천 데이터**로 사용 가능합니다.\n  
국립호남권생물자원관은 고가치 데이터의 **시각화 대시보드**를 통해 민간의 쉽고 빠른 활용을 돕고, 대국민 수요를 충족하고자 합니다.
""")
st.caption('Period of Data : 2024-12-17')
st.write("-" * 50)

# ─────────────────────────────
# ① 종합 정리 문장 (이미지 + 텍스트, 가운데 정렬) — base64 인라인
# ─────────────────────────────
import base64, mimetypes
from pathlib import Path

summary_text = (
    "다수의 국제기관과 연구단체는 생물자원은행이 공공과 민간을 잇는 혁신 플랫폼으로서, "
    "<b>균류·유전자원·천연물 확보 데이터가 민간의 고수요·고가치 산업 영역(식품, 제약, AI 생명정보 등)에 직접 연결될 수 있는 핵심 기반 데이터</b>임을 공통적으로 제시하고 있습니다."
)

@st.cache_data
def image_to_data_uri(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

# 파일명/확장자 정확히 확인 (대소문자 포함)
img_path = "images/79766004-dna-research-with-a-sample-hand-with-a-test-tube-on-a-dna-background.jpg"
data_uri = image_to_data_uri(img_path)

img_html = (
    f'<img src="{data_uri}" alt="biobank summary" width="450" '
    'style="border-radius:10px; margin-bottom:15px;">'
    if data_uri else
    '<div style="color:#999; margin-bottom:8px;">(요약 이미지 파일을 찾을 수 없습니다)</div>'
)

st.markdown(
    f"""
    <div style="
        text-align:center;
        padding: 20px 20px 28px 20px;
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        background: #f8fbff;
        font-size: 1.05rem;
        line-height: 1.6;
    ">
        {img_html}
        <div style="max-width:800px; margin: 0 auto; text-align: center;">
            {summary_text}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


st.write("")  # 여백


# ─────────────────────────────
# ② 기사 탭 (원문 링크 + 요약)
# ─────────────────────────────
st.subheader("DNA 소재 활용성에 대한 국제기관 기사 원문확인")

tab1, tab2, tab3 = st.tabs(["IUCN (국제자연보전연맹)", "BBSA (남아공 생물소재은행협회)", "WEF (세계경제포럼)"])

with tab1:
    st.markdown("### IUCN: *Biobanks: safeguarding biodiversity and preserving hope* (2023)")
    st.markdown("""
    **요약**  
    - 생물자원은행(biobanks)은 **생물다양성 보전**뿐 아니라 **인류 복지·기술혁신**을 위한 **핵심 인프라**임을 강조  
    - 균류·미생물 등 **생물소재 확보 데이터**는 식품·의약·환경 분야에서 **고부가가치 원천소재**로 활용 가능  
    - 공공 데이터가 **민간 R&D**로 이어지는 **가교 역할**을 수행
    """)
    st.link_button("원문 보기 (IUCN)", "https://www.iucn.org/crossroads-blog/202309/biobanks-safeguarding-biodiversity-and-preserving-hope")

with tab2:
    st.markdown("### BBSA: *Preserving Our Past, Protecting Our Future: Why Biodiversity Biobanks Matter* (2024)")
    st.markdown("""
    **요약**  
    - **생물다양성 생물소재은행**이 **식량안보·건강·기술혁신**에 기여한다고 명시  
    - **DNA 및 유전자원 확보 데이터**는 생명공학과 **AI 유전체 분석** 등에서 **핵심 연구 인프라**  
    - 공공기관-민간기업 간 **협력 생태계** 구축의 중요성 제시
    """)
    st.link_button("원문 보기 (BBSA)", "https://bbsa.org.za/2024/03/28/preserving-our-past-protecting-our-future-why-we-need-biodiversity-biobanks/")

with tab3:
    st.markdown("### WEF: *Does Biobanking Hold the Key to Achieving Universal Health?* (2022)")
    st.markdown("""
    **요약**  
    - **고품질 생물표본 + 연계 데이터**가 공중보건 및 **지속가능 산업**의 핵심 요소  
    - 생물소재 데이터는 **민간 연구개발 촉진** 및 **사회적 가치 창출**에 직결  
    - 공공 데이터 기반의 **혁신 가속화** 가능성 강조
    """)
    st.link_button("원문 보기 (WEF)", "https://www.weforum.org/stories/2022/02/does-biobanking-hold-the-key-to-achieving-universal-health/")

st.write("-" * 50)

# ─────────────────────────────
# (참고) 첫 페이지에서 더 이상 개별 기사 본문을 길게 넣지 않습니다.
# 이미지 등 추가 자료가 필요하면, 아래 안내 주석 참고 후 적용하세요.
# - 로컬 이미지 사용 시: 앱 루트에 /images 배치 + 상대경로 사용
# - 외부 이미지 사용 시: 저작권 및 출처 표기 필수
# ─────────────────────────────
