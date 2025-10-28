# 5페이지 Streamlit 앱

## 설치
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

## 실행
streamlit run app.py
# 브라우저: http://localhost:8501

## 데이터 업로드
- pages 2~4 화면에서 CSV 업로드 가능
- 또는 data/ 폴더에 샘플 CSV를 둔 뒤, 화면에서 "샘플 데이터 사용" 체크

## SQLite 위치
- 프로젝트 루트에 board.db 자동 생성 (건의사항 페이지 접속 시)
