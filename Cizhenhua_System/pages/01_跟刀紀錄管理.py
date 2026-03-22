import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time
import streamlit.components.v1 as components

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 樣式終極精修 (數量框邊框 100% 修復版) ---
st.markdown(f"""
<style>
    /* 1. 頁面基礎與護眼背景 */
    .block-container {{ 
        padding-top: 3.3rem !important; 
        padding-bottom: 0.2rem !important; 
        background-color: #F0F9F0 !important; 
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}

    /* 2. 標題大字 */
    .sys-title {{ 
        text-align: center; font-size: 30px !important; font-weight: 900; color: #1e3a8a; 
        margin-top: -15px !important; margin-bottom: 20px !important; 
    }}
    
    /* 3. 標籤文字 (Labels) */
    [data-testid="stWidgetLabel"] p {{
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 5px !important;
    }}

    /* 4. 【數量框與錄入框 邊框全顯化修復】 */
    /* 針對所有輸入元件的共通容器 */
    div[data-baseweb="input"], 
    div[data-baseweb="select"],
    div[data-baseweb="textarea"] {{
        border: 1px solid #1e3a8a !important;
        border-radius: 8px !important;
        height: 48px !important; 
        background-color: white !important;
        box-sizing: border-box !important;
    }}

    /* --- 數量框 (NumberInput) 專屬強化方案 --- */
    .stNumberInput div[data-baseweb="input"] {{
        border: 1px solid #1e3a8a !important; /* 二次確認邊框 */
    }}
    /* 強制讓數量框內的按鈕與背景變透明，避免遮擋框線 */
    .stNumberInput div[data-baseweb="input"] > div {{
        background-color: transparent !important;
    }}
    .stNumberInput input {{
        height: 46px !important; 
        border: none !important;
        background-color: transparent !important;
    }}

    /* --- 備註 (TextArea) 高度與框線 --- */
    .stTextArea div[data-baseweb="textarea"] {{
        height: 48px !important; 
        border: 1px solid #1e3a8a !important;
    }}
    .stTextArea textarea {{
        height: 46px !important;
        min-height: 46px !important;
        padding: 8px 10px !important;
        font-size: 1.1rem !important;
        border: none !important;
        outline: none !important;
        background-color: transparent !important;
    }}

    /* 移除日期元件原生重複邊框 */
    .stDateInput > div {{ border: none !important; }}
    .stDateInput div[data-baseweb="input"] {{ border: 1px solid #1e3a8a !important; }}

    /* 下拉選單文字垂直置中 */
    .stSelectbox [data-baseweb="select"] > div {{
        height: 46px !important;
        display: flex;
        align-items: center;
        padding-left: 10px !important;
    }}

    /* 5. 移除分隔線與頁尾 */
    hr {{ display: none !important; }}
    footer {{visibility: hidden;}}

    /* 6. 分頁標籤樣式 */
    .stTabs [data-baseweb="tab"] {{
        height: 48px; background-color: white; border-radius: 8px; 
        color: #64748b; font-weight: 700; border: 1px solid #e2e8f0;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1e3a8a !important; color: white !important;
    }}

    /* 7. 提交按鈕 */
    div.stButton > button {{ 
        height: 50px !important; width: 100% !important; font-weight: bold !important;
        background-color: #1e3a8a !important; color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# 下方邏輯與介面程式碼 (保持與您上個版本一致，rk_v30 或更新)
# ... [其餘數據核心與 tab 介面程式碼保持不變] ...
