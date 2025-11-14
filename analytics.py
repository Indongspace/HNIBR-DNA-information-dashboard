# analytics.py
import sqlite3
import datetime
import pathlib
import streamlit as st
import pandas as pd

DB_PATH = pathlib.Path("게시판.db")


def _init_db():
    """visit_logs 테이블이 없으면 생성"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS visit_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT NOT NULL,
            date       TEXT NOT NULL,
            page       TEXT NOT NULL,
            session_id TEXT
        )
        """
    )
    conn.commit()
    return conn


def init_session():
    """세션 ID가 없으면 하나 만들어둠"""
    if "session_id" not in st.session_state:
        now = datetime.datetime.now()
        st.session_state["session_id"] = now.strftime("%Y%m%d%H%M%S%f")


def log_visit(page_name: str):
    """각 페이지에서 호출해서 방문 기록 남김"""
    init_session()
    conn = _init_db()

    now = datetime.datetime.now()
    ts = now.isoformat()
    d = now.date().isoformat()
    sid = st.session_state["session_id"]

    conn.execute(
        "INSERT INTO visit_logs (timestamp, date, page, session_id) VALUES (?, ?, ?, ?)",
        (ts, d, page_name, sid),
    )
    conn.commit()
    conn.close()


def load_logs() -> pd.DataFrame:
    """관리자 페이지에서 전체 로그 불러오기"""
    conn = _init_db()
    df = pd.read_sql_query("SELECT * FROM visit_logs", conn)
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
