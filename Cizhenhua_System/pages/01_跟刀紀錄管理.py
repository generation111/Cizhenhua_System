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
    .block-container { padding-top: 3.5rem !important; padding-bottom: 0.2rem !important; }
    .sys-title { 
        text-align: center; 
        font-size: 26px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -10px !important; 
        margin-bottom: 25px !important;
        white-space: nowrap; 
    }
    hr { display: none !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextArea"] label { display: none !important; }
    div[data-testid="stTextArea"] textarea { height: 40px !important; min-height: 40px !important; padding: 8px !important; }
    div.stButton > button { height: 40px !important; width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; }
    footer {visibility: hidden;}
    /* 表格字體微調 */
    .stDataFrame { font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
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
    
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容(含預購)", key=f"cn_{rk}")
    
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_prod = c5.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_pname = c6.text_input("病人名", key=f"pn_{rk}")
    
    c7, c8, c9 = st.columns(3)
    d_hosp = c7.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pid = c9.text_input("病例號/ID", key=f"pi_{rk}")
    
    c10, c11, c12 = st.columns(3)
    d_dept = c10.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    d_qty = c11.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
    d_opname = c12.text_input("手術名稱/部位", key=f"op_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_loc = c13.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c14.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    d_rep = c15.selectbox("跟刀(人員)", OPT.get("rep"), key=f"rp_{rk}")

    bc1, bc2, bc3 = st.columns([0.5, 3.2, 1.3]) 
    with bc1: st.markdown('<p style="font-weight:bold; margin-top:8px;">備註</p>', unsafe_allow_html=True)
    with bc2: d_memo = st.text_area("備註", key=f"me_{rk}", height=40, placeholder="輸入備註...", label_visibility="collapsed")
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.toast("✅ 資料已成功存檔")
                    time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.cache_data.clear() # 提交後清除快取以利同步
                    st.rerun()
                except Exception as e: st.error(f"寫入失敗: {e}")

# --- Tab 2: 歷史紀錄 ---
with tab2:
    st.subheader(" 跟刀紀錄 (Top 50)")
    if ss:
        try:
            ws_res = ss.worksheet("回應試算表")
            all_data = ws_res.get_all_values()
            if len(all_data) > 1:
                df_history = pd.DataFrame(all_data[1:], columns=all_data[0])
                # 倒序顯示，讓最新資料在上面
                st.dataframe(df_history.iloc[::-1].head(50), use_container_width=True, hide_index=True)
            else:
                st.info("目前尚無任何紀錄。")
        except Exception as e:
            st.error(f"讀取紀錄失敗: {e}")
    
    if st.button("🔄 重新整理資料", key="refresh_data"):
        st.cache_data.clear()
        st.rerun()

# --- Tab 3: 預購追蹤 ---
with tab3:
    st.info("💡 此功能連動「產品內容(含預購)」欄位，篩選尚未沖銷之項目。")
    if ss:
        try:
            ws_res = ss.worksheet("回應試算表")
            all_data = ws_res.get_all_values()
            df_all = pd.DataFrame(all_data[1:], columns=all_data[0])
            # 簡單篩選包含「預購」字眼的紀錄
            df_preorder = df_all[df_all['產品內容(含預購)'].str.contains('預購', na=False)]
            st.dataframe(df_preorder.iloc[::-1], use_container_width=True, hide_index=True)
        except:
            st.warning("暫無預購相關數據。")
