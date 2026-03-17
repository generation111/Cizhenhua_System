import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=SYS_TITLE, layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 (標題貼頂) ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    .sys-title { text-align: center; font-size: 26px !important; font-weight: 850; color: #1E3A8A; margin-bottom: 10px !important; }
    footer {visibility: hidden;}
    div.stButton > button { width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線與定義 ---

@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
       if "private_key" in creds_info:
    # 這裡的 strip() 會移除掉所有溢出的隱形字元
    fixed_key = creds_info["private_key"].replace("\\n", "\n").strip()
    creds_info["private_key"] = fixed_key
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except Exception as e:
        # 如果連線失敗，直接顯示完整錯誤，不隱藏
        st.error(f"❌ 連線失敗: {str(e)}")
        return None
ss = get_ss()

@st.cache_data(ttl=600)
def get_options():
    """定義下拉選單內容 (解決 OPT 未定義問題)"""
    # 預設值，防止當機
    default_opt = {"price": ["載入失敗"], "prod": ["載入失敗"], "hosp": ["載入失敗"], "rep": ["載入失敗"]}
    
    if ss is None: return default_opt
    
    try:
        ws_opt = ss.worksheet("Settings") # 務必確認分頁名稱正確
        df_opt = pd.DataFrame(ws_opt.get_all_records())
        return {
            "price": df_opt["批價內容"].dropna().unique().tolist() if "批價內容" in df_opt.columns else ["欄位錯誤"],
            "prod": df_opt["產品項目"].dropna().unique().tolist() if "產品項目" in df_opt.columns else ["欄位錯誤"],
            "hosp": df_opt["使用醫院"].dropna().unique().tolist() if "使用醫院" in df_opt.columns else ["欄位錯誤"],
            "rep": df_opt["業務代表"].dropna().unique().tolist() if "業務代表" in df_opt.columns else ["欄位錯誤"]
        }
    except Exception as e:
        st.warning(f"⚠️ 設定抓取異常: {e}")
        return default_opt

# 執行定義 (這行非常重要，必須在 selectbox 之前)
OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容", key=f"cn_{rk}")
    
    c4, c5, c6 = st.columns(3)
    # 這裡使用 OPT.get 就不會報 NameError
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_prod = c5.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_pname = c6.text_input("病人姓名", key=f"pn_{rk}")
    
    c7, c8, c9 = st.columns(3)
    d_hosp = c7.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pid = c9.text_input("病例號", key=f"pi_{rk}")

    bc1, bc2, bc3 = st.columns([0.3, 3.2, 1])
    with bc2: d_memo = st.text_area("備註", key=f"me_{rk}", height=40, placeholder="輸入備註...")
    with bc3:
        if st.button("🚀 提交數據"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    ws_res.append_row([str(d_date), d_price, d_hosp, d_dr, d_prod, d_spec, d_pname, d_pid, d_memo], value_input_option='USER_ENTERED')
                    st.success("✅ 存檔成功")
                    time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.rerun()
                except: st.error("寫入失敗")
            else: st.error("連線未建立")
