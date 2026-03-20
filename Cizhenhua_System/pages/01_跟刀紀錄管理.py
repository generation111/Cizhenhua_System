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

st.set_page_config(page_title=f"{SYS_TITLE}", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 ---
st.markdown("""
<style>
    .block-container { padding-top: 3.8rem !important; padding-bottom: 1rem !important; }
    .sys-title { 
        text-align: center; 
        font-size: 26px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -30px !important; 
        margin-bottom: 20px !important;
        white-space: nowrap; 
    }
    hr { display: none !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextArea"] label { display: none !important; }
    div[data-testid="stTextArea"] textarea { height: 40px !important; min-height: 40px !important; padding: 8px !important; }
    div.stButton > button { height: 40px !important; width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; }
    footer {visibility: hidden;}
    .stDataFrame { font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線核心 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"❌ 系統連線失敗: {str(e)}")
        return None

ss = get_ss()

@st.cache_data(ttl=60)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_options():
    default_opt = {"price":[], "hosp":[], "dept":[], "prod":[], "loc":["血管攝影室", "開刀房"], "blood":[], "rep":[]}
    if not ss: return default_opt
    try:
        ws = ss.worksheet("Settings")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        return {
            "price": [x for x in df["批價內容"].dropna().unique() if x],
            "hosp": [x for x in df["使用醫院"].dropna().unique() if x],
            "dept": [x for x in df["使用科別"].dropna().unique() if x],
            "prod": [x for x in df["產品項目"].dropna().unique() if x],
            "loc": [x for x in df["使用地點"].dropna().unique() if x] if "使用地點" in df.columns else ["血管攝影室", "開刀房"],
            "blood": [x for x in df["抽血人員"].dropna().unique() if x],
            "rep": [x for x in df["跟刀(操作)人員"].dropna().unique() if x]
        }
    except: return default_opt

OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

# --- Tab 1: 資料登錄 ---
with tab1:
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 第一列
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容(含預購）", key=f"cn_{rk}")
    
    # 第二列：批價內容 + 預購相關欄位
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_pre_total = c5.number_input("預購總量", min_value=0, value=0, key=f"pt_{rk}")
    d_pre_today = c6.number_input("當日批價量", min_value=0, value=0, key=f"py_{rk}")
    
    # 自動計算預購餘量
    d_pre_remain = d_pre_total - d_pre_today
    
    # 第三列
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_pname = c8.text_input("病人名", key=f"pn_{rk}")
    d_pid = c9.text_input("病例號/ID", key=f"pi_{rk}")
    
    # 第四列
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_spec = c11.text_input("規格", key=f"sp_{rk}")
    d_qty = c12.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
    
    # 第五列
    c13, c14, c15 = st.columns(3)
    d_dept = c13.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    d_opname = c14.text_input("手術名稱/使用部位", key=f"op_{rk}")
    d_loc = c15.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    
    # 第六列
    c16, c17, c18 = st.columns(3)
    d_blood = c16.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    d_rep = c17.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    with c18:
        # 顯示即時計算結果給使用者看
        st.metric("預購餘量 (自動計算)", d_pre_remain)

    bc1, bc2, bc3 = st.columns([0.5, 3.2, 1.3]) 
    with bc1: st.markdown('<p style="font-weight:bold; margin-top:8px;">備註</p>', unsafe_allow_html=True)
    with bc2: d_memo = st.text_area("備註說明", key=f"me_{rk}", height=40, placeholder="輸入備註...", label_visibility="collapsed")
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    # 完全對齊您提供的欄位順序寫入
                    row = [
                        str(d_date), d_price, d_hosp, d_dept, d_dr, 
                        d_prod, d_spec, d_qty, d_pre_total, d_pre_today, d_pre_remain, 
                        d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo
                    ]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.toast(f"✅ 資料已存檔！餘量：{d_pre_remain}")
                    time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except Exception as e: st.error(f"寫入失敗: {e}")

# --- Tab 2 & 3 保持邏輯不變 ---
with tab2:
    df_history = fetch_all_data()
    if not df_history.empty:
        st.dataframe(df_history.iloc[::-1].head(50), use_container_width=True, hide_index=True)
        if st.button("🔄 重新整理", key="ref_h"):
            st.cache_data.clear()
            st.rerun()

with tab3:
    df_all = fetch_all_data()
    if not df_all.empty:
        if '預購餘量' in df_all.columns:
            df_all['預購餘量'] = pd.to_numeric(df_all['預購餘量'], errors='coerce').fillna(0)
            df_pre = df_all[df_all['預購餘量'] > 0]
            if not df_pre.empty:
                st.dataframe(df_pre.iloc[::-1], use_container_width=True, hide_index=True)
            else:
                st.info("暫無待結清預購紀錄。")
