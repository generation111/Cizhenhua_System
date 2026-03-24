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

# --- 2. 樣式修復 (對齊截圖的整潔感) ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 2rem !important; background-color: #F8FAFC !important; }}
    .sys-title {{ text-align: center; font-size: 28px; font-weight: 900; color: #1e3a8a; margin-bottom: 20px; }}
    [data-testid="stWidgetLabel"] p {{ font-weight: 700; color: #334155; }}
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important; border: 1px solid #1e3a8a !important; border-radius: 8px !important;
    }}
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
@st.cache_resource
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

def fetch_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        for col in ['預購總量', '當日批價量', '預購餘量']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# --- 4. 主介面 (對齊截圖欄位) ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    rk = st.session_state.rk
    db_df = fetch_data()

    # 第一排：依照截圖順序
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
    d_price = c2.selectbox("批價內容", ["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], key=f"pr_{rk}")
    d_rep = c3.selectbox("代表 (跟刀人員)", ["Eric", "林國慈", "曾子榮"], key=f"rp_{rk}")

    # 第二排
    c4, c5, c6 = st.columns(3)
    d_hosp = c4.selectbox("使用醫院", ["慈濟", "門諾", "國軍", "部花"], key=f"hs_{rk}")
    d_dept = c5.selectbox("使用科別", ["骨科", "一般外科", "神經外科", "復健科"], key=f"dp_{rk}")
    d_dr = c6.text_input("醫師姓名", key=f"dr_{rk}")

    # 第三排
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", ["3E PRP", "Sportvis", "Holisoon", "Biofermin-R", "Nolidin"], key=f"pd_{rk}")
    d_pid = c8.text_input("病例號/ID", key=f"pi_{rk}")
    d_pname = c9.text_input("病人姓名", key=f"pn_{rk}")

    # 第四排：計算區 (預購餘量邏輯)
    st.markdown("---")
    c10, c11, c12 = st.columns(3)
    d_pre_total, d_pre_today, d_qty, can_sub = 0, 0, 0, True

    if d_price == "使用前次預購":
        res_df = db_df[(db_df['病例號/ID'].astype(str).str.strip() == str(d_pid).strip()) & (db_df['產品項目'] == d_prod)]
        cur_bal = int(res_df.iloc[-1]['預購餘量']) if not res_df.empty else 0
        if cur_bal > 0:
            c10.success(f"目前餘量：{cur_bal}")
            d_pre_today = c11.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}")
            d_qty = d_pre_today
        else:
            c10.error("⚠️ 餘額不足"); can_sub = False
    elif d_price == "批價 + 預購":
        d_pre_total = c10.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c11.number_input("當日扣除", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
    else:
        d_qty = c10.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")

    d_memo = st.text_area("備註", key=f"me_{rk}")
    
    if st.button("🚀 提交存檔", use_container_width=True, disabled=not (can_sub and d_pid)):
        latest_df = fetch_data()
        prev_res = latest_df[(latest_df['病例號/ID'].astype(str).str.strip() == str(d_pid).strip()) & (latest_df['產品項目'] == d_prod)]
        prev_bal = int(prev_res.iloc[-1]['預購餘量']) if not prev_res.empty else 0
        
        if d_price == "使用前次預購": final_bal = prev_bal - d_pre_today
        elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal = prev_bal + (d_pre_total - d_pre_today)
        else: final_bal = 0
        
        # 依照試算表標準欄位寫入 (對應您原本的 P2D 邏輯)
        row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, "", d_qty, d_pre_total, d_pre_today, final_bal, "", d_pname, d_pid, "", "", "", d_rep, d_memo]
        ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
        st.toast("✅ 存檔成功！")
        st.cache_data.clear()
        time.sleep(1); st.session_state.rk += 1; st.rerun()

with tab2:
    st.dataframe(fetch_data().iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    track_df = fetch_data()
    if not track_df.empty:
        res = track_df.groupby(['病例號/ID', '產品項目']).tail(1)
        st.dataframe(res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']], use_container_width=True)
