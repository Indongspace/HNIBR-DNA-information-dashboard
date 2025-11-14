import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analytics import log_visit

# Streamlit Multi-page App Configuration (Optional, but good practice)
st.set_page_config(
    page_title="건의사항",
    page_icon="📝",
    layout="wide",
)
log_visit("건의사항")
# ==========================================================
# 세션 상태 및 프론트엔드 유틸리티 함수
# ==========================================================

# 세션 상태 초기화
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "show_write_form" not in st.session_state:
    st.session_state.show_write_form = False
if "admin_ok" not in st.session_state:
    st.session_state["admin_ok"] = False # 관리자 상태 유지
if "posts" not in st.session_state:
    # 건의글을 저장할 리스트 (세션당 유지)
    st.session_state.posts = [] 

# -------------------------------
# 데이터 처리 함수 (세션 상태 기반)
# -------------------------------

def get_total_posts(search_query: str = ""):
    """전체 게시글 수를 반환합니다 (검색 필터링 포함)."""
    if not st.session_state.posts:
        return 0
        
    posts_df = pd.DataFrame(st.session_state.posts)
    
    if not search_query:
        return len(posts_df)
    
    query = search_query.strip().lower()
    # 제목, 작성자 기준으로 필터링
    filtered_df = posts_df[
        posts_df['제목'].str.lower().str.contains(query) | 
        posts_df['작성자'].str.lower().str.contains(query)
    ]
    return len(filtered_df)

def list_posts(limit: int, offset: int, search_query: str = ""):
    """페이지네이션 및 검색 조건에 맞는 게시글 목록을 가져옵니다."""
    
    if not st.session_state.posts:
        return pd.DataFrame({ "번호": [], "제목": [], "작성자": [], "작성일": [], "상태": [] })

    df = pd.DataFrame(st.session_state.posts)

    # 검색 필터링
    if search_query:
        query = search_query.strip().lower()
        df = df[
            df['제목'].str.lower().str.contains(query) | 
            df['작성자'].str.lower().str.contains(query)
        ]

    # 페이지네이션 적용 (최신 글이 위에 오도록 ID 역순으로 정렬)
    df_sorted = df.sort_values(by='번호', ascending=False)
    
    # 목록에 표시할 컬럼만 선택
    display_cols = ["번호", "제목", "작성자", "작성일", "상태"]
    return df_sorted[display_cols].iloc[offset:offset + limit].reset_index(drop=True)

def add_post(author: str, title: str, content: str):
    """세션 상태에 건의글을 추가합니다."""
    
    # 새 게시글 번호 (현재 목록 길이 + 1)
    new_id = len(st.session_state.posts) + 1 
    
    new_post = {
        "번호": new_id,
        "제목": title,
        "작성자": author,
        # 작성 시각을 현재 시각으로 설정
        "작성일": datetime.now().strftime("%Y.%m.%d"),
        "상태": "답변대기", # 초기 상태는 답변대기
        "내용": content # 상세 내용을 위해 내용도 저장
    }
    
    # 세션 상태에 새 글 추가
    st.session_state.posts.append(new_post)


# ==========================================================
# UI 구현
# ==========================================================

# -------------------------------
# 헤더: 제목, 브레드크럼, 검색
# -------------------------------
st.title("건의사항")

# 헤더/검색 레이아웃
header_col1, header_col2 = st.columns([1, 0.4])

with header_col1:
    # 브레드크럼 UI
    st.markdown("<div style='text-align: right; font-size: 14px;'>🏠 <a href='#'>HOME</a> > <a href='#'>게시판</a> > 건의사항</div>", unsafe_allow_html=True)
    
# 검색창
with header_col2:
    search_query = st.text_input(
        "", 
        placeholder="검색어를 입력해주세요", 
        label_visibility="collapsed"
    )

# -------------------------------
# 글 작성 폼 (모달/확장 영역)
# -------------------------------
def render_write_form():
    """글 작성 폼과 관리자 도구를 렌더링합니다."""
    with st.container(border=True):
        st.subheader("새 글 작성 (세션 내 임시 저장)")
        
        # 관리자 도구 (UI만 유지)
        st.caption("관리자 모드를 활성화하면 목록에서 '선택' 및 '상태' 변경 UI가 보입니다.")
        with st.expander("관리자 도구 설정", expanded=False):
            admin_mode = st.checkbox("관리자 모드 활성화", value=st.session_state["admin_ok"])
            
            if admin_mode:
                admin_key = st.text_input("관리자 키", type="password", help="키에 관계없이 UI만 활성화됩니다.")
                st.session_state["admin_ok"] = True
                st.success("관리자 인증 완료 (프론트엔드 모드)")
            else:
                st.session_state["admin_ok"] = False
                st.info("관리자 키를 입력하거나 비활성화하세요.")

        # 실제 글 작성 폼
        with st.form("post_form", clear_on_submit=True):
            author = st.text_input("작성자", max_chars=50, value="익명")
            title = st.text_input("제목", max_chars=100)
            content = st.text_area("내용", height=150, max_chars=2000)
            
            # 버튼 영역 분리
            col_submit, col_cancel = st.columns([1, 1])
            with col_submit:
                submitted = st.form_submit_button("등록", type="primary")
            with col_cancel:
                # 취소 버튼 클릭 시 폼 닫고 새로고침
                if st.form_submit_button("취소"):
                    st.session_state.show_write_form = False
                    st.rerun()

        if submitted:
            if not title.strip() or not content.strip():
                st.warning("제목과 내용을 모두 입력해주세요.")
            else:
                add_post(author.strip(), title.strip(), content.strip())
                st.success(f"건의사항 '{title}'이(가) 세션에 저장되었습니다!")
                st.session_state.show_write_form = False # 폼 닫기
                st.rerun()

# 폼 표시 로직
if st.session_state.show_write_form:
    render_write_form()
    st.divider() # 구분선 추가

# -------------------------------
# 목록 표시
# -------------------------------

# 페이지네이션 설정
posts_per_page = 10 # 페이지당 10개로 고정
total_posts = get_total_posts(search_query=search_query) 
total_pages = int(np.ceil(total_posts / posts_per_page))
offset = (st.session_state.current_page - 1) * posts_per_page

# 게시글 데이터 가져오기
posts_df = list_posts(limit=posts_per_page, offset=offset, search_query=search_query)

# CSS 스타일 정의
st.markdown("""
    <style>
    /* 상태 표시 색상 */
    .답변대기 { color: #d62728; font-weight: bold; } /* 빨간색 계열 */
    .답변완료 { color: #2ca02c; font-weight: bold; } /* 초록색 */
    /* 테이블 헤더/경계 스타일 */
    .st-emotion-cache-1r6r0y9 { 
        border-bottom: 2px solid #333;
    }
    </style>
""", unsafe_allow_html=True)


if posts_df.empty:
    st.info("작성된 건의사항이 없습니다.")
else:
    # 관리자 모드일 경우 삭제 체크박스를 포함할 컬럼 구성
    if st.session_state.get("admin_ok"):
        # posts_df에 '선택' 컬럼 추가 (data_editor에서 사용)
        posts_df.loc[:, "선택"] = False
        columns = ["선택", "번호", "제목", "작성자", "작성일", "상태"]
    else:
        columns = ["번호", "제목", "작성자", "작성일", "상태"]

    # set_index('번호')를 사용하면 '번호'가 컬럼에서 제외되므로,
    # columns 리스트에서 '번호'를 제외한 리스트를 만들어 사용합니다.
    display_columns = [col for col in columns if col != "번호"]
    
    # Streamlit Table/DataFrame 표시 (편집 가능한 상태로 렌더링)
    st.data_editor(
        posts_df.set_index('번호')[display_columns],
        key="posts_editor",
        use_container_width=True,
        column_config={
            "제목": st.column_config.Column(
                "제목",
                help="클릭하면 상세 내용을 볼 수 있습니다. (기능 미구현)",
                width="large"
            ),
            "상태": st.column_config.SelectboxColumn(
                "상태",
                options=["답변대기", "답변완료"],
                disabled=not st.session_state.get("admin_ok") # 관리자가 아니면 편집 불가
            ),
            "선택": st.column_config.CheckboxColumn(
                "선택",
                help="삭제할 글을 선택합니다.",
                disabled=not st.session_state.get("admin_ok")
            ),
        },
        hide_index=False,
        # 프론트엔드 모드에서는 편집 잠금 (선택/상태는 위에서 따로 해제)
        disabled=[col for col in display_columns if col not in ['선택', '상태']] 
    )
    
    # -------------------------------
    # 삭제 기능 (관리자 전용) - UI만 유지
    # -------------------------------
    if st.session_state.get("admin_ok"):
        st.warning("경고: 현재 프론트엔드 모드입니다. 아래 버튼을 눌러도 데이터가 영구적으로 삭제되거나 상태가 변경되지 않습니다. (세션 내에서만 변경 가능)")
        
        # 실제 삭제/상태 변경 로직 (세션 상태 반영)
        editor_data = st.session_state["posts_editor"]
        
        # 1. 삭제 로직 (선택된 항목이 있는 경우)
        selected_indices = [idx for idx, selected in enumerate(editor_data['선택']) if selected]
        
        if selected_indices:
            if st.button("선택된 건의사항 삭제", type="secondary"):
                # 실제 st.session_state.posts에서 해당 번호의 항목을 찾아 제거해야 합니다.
                
                # 현재 페이지에 표시된 글의 번호 목록
                current_page_post_numbers = posts_df.set_index('번호').index.tolist()
                
                # 삭제할 글의 번호
                posts_to_delete_numbers = [current_page_post_numbers[i] for i in selected_indices]
                
                # 세션 상태 업데이트: 삭제할 번호가 아닌 글만 남김
                st.session_state.posts = [
                    post for post in st.session_state.posts 
                    if post['번호'] not in posts_to_delete_numbers
                ]
                st.toast(f"{len(posts_to_delete_numbers)}개 건의글이 세션에서 삭제되었습니다.")
                st.rerun()

        # 2. 상태 변경 로직 (data_editor의 변화를 감지하여 세션에 반영)
        # 이 부분은 data_editor가 변경되면 자동으로 st.session_state["posts_editor"]에 반영되므로
        # 실제 DB라면 업데이트 쿼리를 날려야 하지만, 여기서는 임시로 처리합니다.
        # Streamlit은 st.data_editor의 변경 시 리턴 값으로 변경된 DataFrame을 제공하지 않고
        # st.session_state를 통해 접근해야 합니다. (복잡하므로 삭제만 명확히 구현하고 상태 변경은 UI만 표시)


st.divider()

# -------------------------------
# 하단: 페이지네이션 및 글쓰기 버튼
# -------------------------------

# 페이지네이션 (번호 버튼 스타일)
page_cols = st.columns([1] * 5 + [4]) # 페이지 번호 컬럼과 나머지 공간 분리

if total_posts > 0:
    # 페이지네이션 버튼이 표시되는 경우
    
    # 페이지네이션 로직 (이전 버전과 동일)
    total_pages = int(np.ceil(total_posts / posts_per_page))
    start_page = max(1, st.session_state.current_page - 2)
    end_page = min(total_pages, st.session_state.current_page + 2)
    
    # << (처음), < (이전) 버튼
    current_col_index = 0
    
    if st.session_state.current_page > 1:
        with page_cols[0]:
            if st.button("«", key="first_page"):
                st.session_state.current_page = 1
                st.rerun()
        with page_cols[1]:
            if st.button("<", key="prev_page"):
                st.session_state.current_page = max(1, st.session_state.current_page - 1)
                st.rerun()
        current_col_index = 2

    # 페이지 번호 버튼 (최대 5개 컬럼 사용)
    for i in range(start_page, end_page + 1):
        if current_col_index >= 5:
            break
        
        with page_cols[current_col_index]:
            is_active = (i == st.session_state.current_page)
            # 현재 페이지는 Primary 스타일 적용
            if st.button(str(i), key=f"page_{i}", type="primary" if is_active else "secondary"):
                st.session_state.current_page = i
                st.rerun()
        current_col_index += 1

    # > (다음), » (마지막) 버튼
    if st.session_state.current_page < total_pages:
        with page_cols[current_col_index]:
            if st.button(">", key="next_page"):
                st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                st.rerun()
        with page_cols[current_col_index + 1]:
            if st.button("»", key="last_page"):
                st.session_state.current_page = total_pages
                st.rerun()

    # '글쓰기' 버튼을 페이지네이션 옆에 배치
    col_write = page_cols[-1]
    
else:
    # total_posts가 0일 경우 페이지네이션 버튼이 표시되지 않고,
    # '글쓰기' 버튼을 표시하기 위해 컬럼을 다시 정의합니다.
    col_write, col_empty = st.columns([1, 8])

    
# 글쓰기 버튼 (우측 하단)
with col_write:
    if st.button("글쓰기", key="write_button_bottom", use_container_width=True, type="primary"):
        st.session_state.show_write_form = True
        st.rerun()


st.caption("ⓒ 게시판 모듈 · Streamlit 프론트엔드 전용 (세션 상태 저장)")