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

st.set_page_config(page_title=SYS_TITLE, layout="centered", initial_sidebar_state="collapsed")

# --- 2. 樣式精修 (解決標題切割問題) ---
st.markdown(f"""
<style>
      /* 修正 Padding-top 避免標題切割，並保持綠色基底 */
    .block-container {{ 
        padding-top: 4rem !important; 
        max-width: 900px !important;
        background-color: #F0F9F0 !important; 
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    
    /* 標題樣式 */
    .sys-title {{ 
        text-align: center; 
        font-size: 32px !important; 
        font-weight: 900; 
        color: #1e3a8a; 
        margin-top: -20px !important;
        margin-bottom: 25px !important; 
    }}
    
    /* 欄位標籤與輸入框 */
    [data-testid="stWidgetLabel"] p {{ font-size: 1.15rem !important; font-weight: 700 !important; color: #1e293b !important; }}
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important; border: 2px solid #1e3a8a !important; border-radius: 8px !important; height: 45px !important;
    }}
    
    /* Tab 樣式 */
    .stTabs [data-baseweb="tab"] {{
        height: 55px !important; background-color: white; font-weight: 800 !important; font-size: 1.3rem !important;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #1e3a8a !important; color: white !important; }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 3. 數據核心 ---
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
        num_cols = ['預購總量', '當日批價量', '預購餘量', '數量']
        for col in num_cols:
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
    except: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], "hosp":[], "dept":[], "prod":["3E PRP"], "rep":["Eric", "林國慈", "曾子榮"]}

OPT = get_options()

# --- 4. 介面佈局 ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v34" not in st.session_state: st.session_state.rk_v34 = 0
    rk = st.session_state.rk_v34
    db_df = fetch_all_data()

    # 第一列
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容(含預購)", key=f"cn_{rk}")
    
    # 第二列 (預購邏輯區)
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_pre_total, d_pre_today, d_qty, can_sub = 0, 0, 0, True

    if d_price == "使用前次預購":
        p_now = st.session_state.get(f"pi_{rk}", "").strip()
        pr_now = st.session_state.get(f"pd_{rk}", "")
        u_df = db_df[(db_df['病例號/ID'].astype(str).str.strip() == p_now) & (db_df['產品項目'] == pr_now)]
        bal = int(u_df.iloc[-1]['預購餘量']) if not u_df.empty else 0
        if bal > 0:
            c6.success(f"目前餘量：{bal}")
            d_pre_today = c5.number_input("扣除量", min_value=1, max_value=bal, value=1, key=f"py_{rk}"); d_qty = d_pre_today
        else:
            c5.warning("無餘額"); can_sub = False
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日扣除", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    else:
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty

    # 第三列
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")
    
    # 第四列
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    # 第五列
    c13, c14, c15 = st.columns(3)
    d_op = c13.text_input("手術/部位", key=f"op_{rk}")
    d_loc = c14.selectbox("地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    # 第六列
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    d_memo = c17.text_area("備註", key=f"me_{rk}")
    
    if c18.button("🚀 提交數據", use_container_width=True, disabled=not (can_sub and d_pid)):
        temp_df = fetch_all_data()
        prev_res = temp_df[(temp_df['病例號/ID'].astype(str).str.strip() == d_pid.strip()) & (temp_df['產品項目'] == d_prod)]
        curr_bal = int(prev_res.iloc[-1]['預購餘量']) if not prev_res.empty else 0
        
        if d_price == "使用前次預購": final_bal = curr_bal - d_pre_today
        elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal = curr_bal + (d_pre_total - d_pre_today)
        else: final_bal = 0
        
        row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, final_bal, d_content, d_pname, d_pid, d_op, d_loc, d_blood, d_rep, d_memo]
        ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
        st.toast("✅ 已存檔！")
        st.cache_data.clear()
        time.sleep(1); st.session_state.rk_v34 += 1; st.rerun()

with tab2:
    st.dataframe(fetch_all_data().iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    t_df = fetch_all_data()
    if not t_df.empty:
        res = t_df.groupby(['病例號/ID', '產品項目']).tail(1)
        st.dataframe(res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']], use_container_width=True, hide_index=True)
