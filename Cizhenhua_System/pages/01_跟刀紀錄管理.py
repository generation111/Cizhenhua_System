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

# --- 2. 樣式優化 (佰哥調校：5rem / 0.2rem) ---
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

@st.cache_data(ttl=5)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        return pd.DataFrame()
    except: return pd.DataFrame()

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

with tab1:
    if "rk_v14" not in st.session_state: st.session_state.rk_v14 = 0
    rk = st.session_state.rk_v14
    
    # 用於顯示提交結果的空容器
    msg_container = st.empty()
    
    # 區塊 1
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_pid = c3.text_input("病例號/ID (自動對帳)", key=f"pi_{rk}")
    
    st.markdown("---")
    
    # 區塊 2 (對帳用)
    cp1, cp2, cp3 = st.columns(3)
    d_prod = cp1.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = cp2.text_input("規格", key=f"sp_{rk}")
    d_content = cp3.text_input("使用內容", key=f"cn_{rk}")

    st.markdown("---")

    # 區塊 3：批價邏輯
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    d_pre_total, d_pre_today, d_qty = 0, 0, 0
    can_submit = True 

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
    elif d_price == "使用前次預購":
        if not d_pid:
            st.warning("👈 請輸入 ID")
            can_submit = False
        else:
            df_history = fetch_all_data()
            if not df_history.empty:
                user_record = df_history[(df_history['病例號/ID'] == d_pid) & (df_history['產品項目'] == d_prod)]
                total_pre = pd.to_numeric(user_record['預購總量'], errors='coerce').sum()
                total_used = pd.to_numeric(user_record['當日批價量'], errors='coerce').sum()
                current_balance = total_pre - total_used
                if current_balance > 0:
                    st.success(f"✅ {d_prod} 餘量：{int(current_balance)}")
                    d_pre_today = c5.number_input(f"扣除量", min_value=1, max_value=int(current_balance), value=1, key=f"py_{rk}")
                    d_qty, d_pre_total = d_pre_today, 0
                else:
                    st.error(f"❌ {d_prod} 餘額為 0")
                    can_submit = False
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_qty = 0

    d_pre_remain = d_pre_total - d_pre_today if d_price != "使用前次預購" else 0
    st.markdown("---")

    # 區塊 4
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
    with c17:
        d_memo = st.text_area("備註", key=f"me_{rk}", height=40, label_visibility="collapsed")
    with c18:
        if st.button("🚀 提交數據", key="submit_btn", disabled=not can_submit):
            with st.spinner("傳輸中..."):
                try:
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, d_pre_remain, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    
                    # 只有真正成功才顯示
                    msg_container.success("✅ 數據存檔成功！已自動同步歷史紀錄。")
                    time.sleep(1.5)
                    st.session_state.rk_v14 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except Exception as e:
                    # 顯示具體錯誤，避免假性失敗
                    msg_container.error(f"❌ 傳輸不穩定 (已連線但未收到確認)，請查看歷史紀錄。")

# 歷史紀錄與預購
with tab2:
    df_h = fetch_all_data()
    if not df_h.empty:
        st.dataframe(df_h.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    df_all = fetch_all_data()
    if not df_all.empty:
        df_all['預購餘量'] = pd.to_numeric(df_all['預購餘量'], errors='coerce').fillna(0)
        df_pre = df_all[df_all['預購餘量'] > 0]
        st.dataframe(df_pre.iloc[::-1], use_container_width=True, hide_index=True)
