import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "2026 年度跟刀紀錄管理系統"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 ---
st.markdown("""
<style>
    .block-container { padding-top: 3em !important; padding-bottom: 0rem !important; }
    .sys-title { text-align: center; font-size: 26px !important; font-weight: 850; color: #1E3A8A; margin-top: -10px !important; margin-bottom: 15px !important; }
    hr { display: none !important; }
    .stTabs [data-baseweb="tab-list"] { margin-bottom: 10px !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextArea"] label { display: none !important; }
    div[data-testid="stTextArea"] textarea { height: 40px !important; min-height: 40px !important; padding: 8px !important; border-radius: 5px !important; }
    div.stButton > button { height: 40px !important; width: 100% !important; font-size: 16px !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; color: #1E3A8A !important; background-color: #FFF !important; border-radius: 5px !important; transition: 0.3s; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

# --- 修正後的連線與讀取邏輯 ---
# 1. 確保分頁名稱是 "Settings"
@st.cache_data(ttl=600)
def get_options():
    default_opt = {
        "price": ["載入中"], "prod": ["載入中"], "hosp": ["載入中"], 
        "rep": ["載入中"], "dept": ["載入中"], "blood": ["載入中"]
    }
    
    if ss is None: # 如果 Secrets 格式錯誤，ss 就會是 None
        return default_opt
        
    try:
        ws_opt = ss.worksheet("Settings") # 這裡已配合您的試算表名稱改為 Settings
        df_opt = pd.DataFrame(ws_opt.get_all_records())
        
        # 這裡回傳一個字典 (Dictionary)
        return {
            "price": df_opt["批價內容"].dropna().unique().tolist(),
            "prod": df_opt["產品項目"].dropna().unique().tolist(),
            "hosp": df_opt["使用醫院"].dropna().unique().tolist(),
            "rep": df_opt["業務代表"].dropna().unique().tolist(),
            "dept": df_opt["使用科別"].dropna().unique().tolist() if "使用科別" in df_opt.columns else ["載入中"],
            "blood": df_opt["抽血人員"].dropna().unique().tolist() if "抽血人員" in df_opt.columns else ["載入中"]
        }
    except Exception as e:
        return default_opt

# 2. 確保 OPT 是一個字典
OPT = get_options()

# 3. 在 selectbox 調用時，請這樣寫（確保 OPT 是字典後才能用 .get()）
if isinstance(OPT, dict):
        d_price = c4.selectbox("批價內容", OPT.get("price", ["載入中"]), key="price_key")
    else:
        st.error("系統無法載入設定清單，請檢查連線")
OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 第一排
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容-含預購", key=f"cn_{rk}")
    
    # 第二排
    c4, c5, c6 = st.columns(3)
    if isinstance(OPT, dict):
        d_price = c4.selectbox("批價內容", OPT.get("price", ["載入中"]), key=f"price_{rk}")
        d_prod = c5.selectbox("產品項目", OPT.get("prod", ["載入中"]), key=f"prod_{rk}")
    else:
        st.error("設定格式錯誤")
        d_price, d_prod = "錯誤", "錯誤"
    d_pname = c6.text_input("病人姓名", key=f"pn_{rk}") # 補上缺失的變數定義
    
    # 第三排
    c7, c8, c9 = st.columns(3)
    d_hosp = c7.selectbox("使用醫院", OPT.get("hosp", ["載入中"]), key=f"hs_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pid = c9.text_input("病例號/ID", key=f"pi_{rk}")
    
    # 第四排
    c10, c11, c12 = st.columns(3)
    d_dept = c10.selectbox("使用科別", OPT.get("dept", ["載入中"]), key=f"dp_{rk}")
    d_qty = c11.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
    d_opname = c12.text_input("手術名稱/使用部位", key=f"op_{rk}")
    
    # 第五排
    c13, c14, c15 = st.columns(3)
    d_loc = c13.selectbox("使用地點", ["血管攝影室", "開刀房"], key=f"lc_{rk}")
    d_blood = c14.selectbox("抽血人員", OPT.get("blood", ["載入中"]), key=f"bl_{rk}")
    d_rep = c15.selectbox("跟刀(操作)人員", OPT.get("rep", ["載入中"]), key=f"rp_{rk}")

    # 底欄單列
    bc1, bc2, bc3 = st.columns([0.3, 3.2, 1])
    with bc1: st.markdown('<p style="font-weight:bold; margin-bottom:0px;">備註</p>', unsafe_allow_html=True)
    with bc2: d_memo = st.text_area("", key=f"me_{rk}", height=40, placeholder="請輸入備註...")
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            with st.spinner("存檔中..."):
                try:
                    ws_res = ss.worksheet("回應試算表")
                    # 按照試算表欄位順序對齊
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.cache_data.clear()
                    st.toast("✅ 資料已成功存檔"); time.sleep(1); st.session_state.rk_v11 += 1; st.rerun()
                except Exception as e: st.error(f"寫入失敗: {e}")
