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

# --- 2. 樣式優化 (佰哥規格：5rem / 0.2rem) ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 5rem !important; padding-bottom: 0.2rem !important; }}
    .sys-title {{ 
        text-align: center; font-size: 26px !important; font-weight: 850; color: #1E3A8A; 
        margin-top: -30px !important; margin-bottom: 5px !important; white-space: nowrap; 
    }}
    hr {{ border: 0 !important; border-top: 1px solid #e6e9ef !important; margin: 5px 0 !important; padding: 0 !important; }}
    [data-testid="stVerticalBlock"] {{ gap: 0.5rem !important; }}
    div.stButton > button {{ height: 40px !important; width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; }}
    footer {{visibility: hidden;}}
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
    except: return None

ss = get_ss()

@st.cache_data(ttl=2)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            df['病例號/ID'] = df['病例號/ID'].astype(str).str.strip()
            df['產品項目'] = df['產品項目'].astype(str).str.strip()
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 4. 核心餘額計算邏輯 (用於顯示與提交寫入) ---
def get_current_balance(df, pid, prod):
    if df.empty or not pid: return 0
    user_record = df[(df['病例號/ID'] == pid) & (df['產品項目'] == prod)]
    # 總寄庫 = 批價+預購(預購總量) + 純預購(預購總量)
    total_in = pd.to_numeric(user_record[user_record['批價內容'].isin(['批價 + 預購', '純預購寄庫'])]['預購總量'], errors='coerce').sum()
    # 總消耗 = 批價+預購(當日量) + 使用前次(當日量) + 使用他人(當日量)
    total_out = pd.to_numeric(user_record[user_record['批價內容'].isin(['批價 + 預購', '使用前次預購', '使用他人預購'])]['當日批價量'], errors='coerce').sum()
    return int(total_in - total_out)

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
            "loc": [x for x in df["使用地點"].dropna().unique() if x] if "使用地點" in df.columns else ["血管攝影室", "開刀房"],
            "blood": [x for x in df["抽血人員"].dropna().unique() if x],
            "rep": [x for x in df["跟刀(操作)人員"].dropna().unique() if x]
        }
    except: return {"price":[], "hosp":[], "dept":[], "prod":[], "loc":[], "blood":[], "rep":[]}

OPT = get_options()

# --- 5. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v18" not in st.session_state: st.session_state.rk_v18 = 0
    rk = st.session_state.rk_v18
    msg_container = st.empty()
    
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_pid = c3.text_input("病例號/ID (自動對帳)", key=f"pi_{rk}").strip()
    
    cp1, cp2, cp3 = st.columns(3)
    d_prod = cp1.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = cp2.text_input("規格", key=f"sp_{rk}")
    d_content = cp3.text_input("使用內容", key=f"cn_{rk}")

    st.markdown("---")

    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    d_pre_total, d_pre_today, d_qty = 0, 0, 0
    can_submit = True 
    db_df = fetch_all_data()
    real_balance = get_current_balance(db_df, d_pid, d_prod)

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
        st.info(f"💡 目前剩餘：{real_balance} -> 預購後將變為：{real_balance + d_pre_total - d_pre_today}")
    elif d_price == "使用前次預購":
        if real_balance > 0:
            st.success(f"✅ {d_prod} 累計餘量：{real_balance}")
            d_pre_today = c5.number_input(f"扣除量", min_value=1, max_value=real_balance, value=1, key=f"py_{rk}")
            d_qty = d_pre_today
        else:
            st.error(f"❌ {d_prod} 餘額為 0")
            can_submit = False
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_qty = 0

    st.markdown("---")

    # 其他欄位保持原樣...
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pname = c11.text_input("病人名", key=f"pn_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術/部位", key=f"op_{rk}")
    d_loc = c14.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀人員", OPT.get("rep"), key=f"rp_{rk}")
    with c17: d_memo = st.text_area("備註", key=f"me_{rk}", height=40, label_visibility="collapsed")
    
    with c18:
        if st.button("🚀 提交數據", key="submit_btn", disabled=not can_submit):
            with st.spinner("存檔中..."):
                try:
                    # 【遞扣核心】：重新計算本次寫入 L 欄的餘額
                    new_df = fetch_all_data()
                    latest_bal = get_current_balance(new_df, d_pid, d_prod)
                    
                    if d_price == "單次批價使用": d_pre_remain = 0
                    elif d_price == "使用前次預購": d_pre_remain = latest_bal - d_pre_today
                    else: d_pre_remain = latest_bal + d_pre_total - d_pre_today
                    
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, d_pre_remain, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    
                    msg_container.success(f"✅ 存檔成功！餘量已遞扣至：{d_pre_remain}")
                    time.sleep(1)
                    st.session_state.rk_v18 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except: msg_container.error("提交失敗")

# --- 🔍 追蹤表單 (維持正確計算) ---
with tab3:
    df_all = fetch_all_data()
    if not df_all.empty:
        summary = df_all.groupby(['病例號/ID', '產品項目']).apply(
            lambda x: get_current_balance(x, x.name[0], x.name[1])
        ).reset_index(name='剩餘總量')
        st.dataframe(summary[summary['剩餘總量'] > 0], use_container_width=True, hide_index=True)
