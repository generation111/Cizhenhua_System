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

# 設定頁面：標題與佈局
st.set_page_config(page_title=f"{SYS_TITLE}", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 (標題貼齊上緣) ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    .sys-title { text-align: center; font-size: 26px !important; font-weight: 850; color: #1E3A8A; margin-bottom: 10px !important; }
    hr { display: none !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextArea"] label { display: none !important; }
    div[data-testid="stTextArea"] textarea { height: 40px !important; min-height: 40px !important; }
    div.stButton > button { height: 40px !important; width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; color: #1E3A8A !important; background-color: #FFF !important; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線邏輯 ---

# --- 3. 數據連線 ---

@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info:
            # 修正換行並去除空白，解決 InvalidPadding 問題
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"❌ 連線失敗: {str(e)}")
        return None

# 先初始化連線
ss = get_ss()

# 【這部分您之前漏掉了】定義如何取得選項
@st.cache_data(ttl=600)
def get_options():
    # 預設選項，防止連線失敗時 OPT 變數不存在
    default_opt = {
        "price": ["載入失敗"], "prod": ["載入失敗"], 
        "hosp": ["載入失敗"], "rep": ["載入失敗"]
    }
    
    if ss is None:
        return default_opt
        
    try:
        # 指向您的 Settings 分頁
        ws_opt = ss.worksheet("Settings")
        df_opt = pd.DataFrame(ws_opt.get_all_records())
        
        # 轉換成清單字典
        return {
            "price": df_opt["批價內容"].dropna().unique().tolist() if "批價內容" in df_opt.columns else ["欄位錯誤"],
            "prod": df_opt["產品項目"].dropna().unique().tolist() if "產品項目" in df_opt.columns else ["欄位錯誤"],
            "hosp": df_opt["使用醫院"].dropna().unique().tolist() if "使用醫院" in df_opt.columns else ["欄位錯誤"],
            "rep": df_opt["業務代表"].dropna().unique().tolist() if "業務代表" in df_opt.columns else ["欄位錯誤"]
        }
    except Exception as e:
        st.warning(f"⚠️ 讀取 Settings 分頁失敗: {e}")
        return default_opt

OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    # 使用 session_state 確保提交後頁面重置
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 第一排
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容", key=f"cn_{rk}")
    
    # 第二排
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price", ["載入中"]), key=f"pr_{rk}")
    d_prod = c5.selectbox("產品項目", OPT.get("prod", ["載入中"]), key=f"pd_{rk}")
    d_pname = c6.text_input("病人姓名", key=f"pn_{rk}")
    
    # 第三排
    c7, c8, c9 = st.columns(3)
    d_hosp = c7.selectbox("使用醫院", OPT.get("hosp", ["載入中"]), key=f"hs_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pid = c9.text_input("病例號", key=f"pi_{rk}")

    # 底欄
    bc1, bc2, bc3 = st.columns([0.3, 3.2, 1])
    with bc1: st.write("**備註**")
    with bc2: d_memo = bc2.text_area("", key=f"me_{rk}", height=40)
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    ws_res.append_row([
                        str(d_date), d_price, d_hosp, d_dr, d_prod, 
                        d_spec, d_pname, d_pid, d_memo
                    ], value_input_option='USER_ENTERED')
                    st.toast("✅ 存檔成功")
                    time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"寫入失敗：{e}")
            else:
                st.error("連線未建立，無法存檔")
