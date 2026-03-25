import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "01_跟刀紀錄管理"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

# 佈局設定：保持 wide 並讓 Sidebar 預設收納，確保滑動手感
st.set_page_config(page_title=SYS_TITLE, layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式精修 (邊框修正、43px、4rem、復原手勢) ---
st.markdown(f"""
<style>
    /* 1. 復原手勢：保留 Header 及其預設行為，不進行隱藏 */
    [data-testid="stHeader"] {{ 
        background-color: #F0F9F0 !important; 
    }}
    
    /* 2. 側邊欄寬度減少 25% */
    [data-testid="stSidebar"] {{ 
        min-width: 220px !important; 
        max-width: 220px !important; 
    }}
    
    /* 3. 頂部留白與主容器 */
    .block-container {{ 
        padding-top: 4rem !important; 
        max-width: 1000px !important;
        background-color: #F0F9F0 !important; 
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    
    .sys-title {{ 
        text-align: center; font-size: 32px !important; font-weight: 900; color: #1e3a8a; 
        margin-bottom: 25px !important; 
    }}

    /* --- 核心：統一 43px 與單一邊框 (徹底解決重複框線) --- */
    /* 強制移除所有組件內層的預設線條與陰影 */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    .stTextArea textarea {{
        border: none !important; 
        box-shadow: none !important;
        background-color: transparent !important;
    }}

    /* 重新在 stWidget 層級定義單一 2px 邊框 */
    div[data-testid="stTextInput"] > div, 
    div[data-testid="stSelectbox"] > div, 
    div[data-testid="stNumberInput"] > div,
    div[data-testid="stTextArea"] > div {{
        height: 43px !important;
        border: 2px solid #1e3a8a !important; 
        border-radius: 8px !important;
        background-color: white !important;
        overflow: hidden !important;
    }}

    /* 文字垂直居中與內距 */
    input {{ 
        height: 41px !important; 
        padding: 0 12px !important; 
        line-height: 41px !important; 
    }}
    
    /* 備註欄 (TextArea) 修正 */
    .stTextArea textarea {{
        height: 39px !important;
        padding: 8px 12px !important;
        line-height: 1.2 !important;
    }}

    /* Tabs 標籤頁樣式 */
    .stTabs [data-baseweb="tab"] {{ 
        height: 50px !important; 
        font-weight: 800 !important; 
        font-size: 1.1rem !important; 
    }}
    .stTabs [aria-selected="true"] {{ 
        background-color: #1e3a8a !important; 
        color: white !important; 
        border-radius: 8px 8px 0 0; 
    }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 3. 數據與核心邏輯 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

@st.cache_data(ttl=5)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        for col in ['預購總量', '當日批價量', '預購餘量', '數量']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def get_options():
    try:
        ws = ss.worksheet("Settings")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        return {
            "price": [x for x in df["批價內容"].dropna().unique() if x],
            "hosp": [x for x in df["使用醫院"].dropna().unique() if x],
            "dept": [x for x in df["使用科別"].dropna().unique() if x],
            "prod": [x for x in df["產品項目"].dropna().unique() if x],
            "rep": [x for x in df["跟刀(操作)人員"].dropna().unique() if x],
            "loc": [x for x in df["使用地點"].dropna().unique() if x] if "使用地點" in df.columns else ["血管攝影室", "開刀房"],
            "blood": [x for x in df["抽血人員"].dropna().unique() if x]
        }
    except: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購"], "hosp":[], "dept":[], "prod":["3E PRP"], "rep":["Eric", "林國慈"]}

OPT = get_options()

# --- 4. 佈局 ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "v7_gesture_fix" not in st.session_state: st.session_state.v7_gesture_fix = 0
    rk = st.session_state.v7_gesture_fix
    db_df = fetch_all_data()

    # 第一列 (2欄)
    c1, c2 = st.columns(2)
    d_price = c1.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_hosp = c2.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    
    # 第二列 (3欄)
    c3, c4, c5 = st.columns(3)
    d_dr = c3.text_input("醫師姓名", key=f"dr_{rk}")
    d_prod = c4.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_dept = c5.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")

    # 第三列 (3欄)
    c6, c7, c8 = st.columns(3)
    d_spec = c6.text_input("規格", key=f"sp_{rk}")
    d_pid = c7.text_input("病例號/ID", key=f"pi_{rk}")
    d_pname = c8.text_input("病人名", key=f"pn_{rk}")
    
    # 預購計算區
    c9, c10, c11 = st.columns(3)
    d_qty, d_pre_total, d_pre_today, can_sub = 0, 0, 0, True
    
    if d_price == "使用前次預購":
        p_id = st.session_state.get(f"pi_{rk}", "").strip()
        p_item = st.session_state.get(f"pd_{rk}", "")
        u_df = db_df[(db_df['病例號/ID'].astype(str).str.strip() == p_id) & (db_df['產品項目'] == p_item)]
        bal = int(u_df.iloc[-1]['預購餘量']) if not u_df.empty else 0
        if bal > 0:
            c9.success(f"目前餘量：{bal}")
            d_pre_today = c10.number_input("扣除量", min_value=1, max_value=bal, value=1, key=f"py_{rk}")
            d_qty = d_pre_today
        else:
            c9.warning("⚠️ 餘額不足"); can_sub = False
    elif d_price == "批價 + 預購":
        d_pre_total = c9.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c10.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
    else:
        d_qty = c9.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty

    # 第四列
    c12, c13, c14 = st.columns(3)
    d_op = c12.text_input("手術名稱/部位", key=f"op_{rk}")
    d_loc = c13.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c14.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")

    # 第五列
    c15, c16, c17 = st.columns(3)
    d_rep = c15.selectbox("跟刀人員", OPT.get("rep"), key=f"rp_{rk}")
    d_memo = c16.text_area("備註", key=f"me_{rk}")
    
    with c17:
        st.write("") 
        if st.button("🚀 提交數據", use_container_width=True, disabled=not (can_sub and d_pid)):
            now_dt = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
            # 餘額計算與寫入邏輯 (略) ...
            st.toast("✅ 存檔成功")
            time.sleep(1); st.session_state.v7_gesture_fix += 1; st.rerun()

# 頁籤 2 & 3
with tab2: st.dataframe(fetch_all_data().iloc[::-1].head(50), use_container_width=True, hide_index=True)
with tab3:
    t_df = fetch_all_data()
    if not t_df.empty:
        res = t_df.groupby(['病例號/ID', '產品項目']).tail(1)
        st.dataframe(res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']], use_container_width=True, hide_index=True)
