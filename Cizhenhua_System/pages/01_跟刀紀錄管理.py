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

# --- 2. 樣式優化 (嚴格遵守佰哥 5rem/0.2rem 參數) ---
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
    if "rk_v12" not in st.session_state: st.session_state.rk_v12 = 0
    rk = st.session_state.rk_v12
    
    # 第一區：醫師與 ID
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_pid = c3.text_input("病例號/ID (輸入後自動對帳)", key=f"pi_{rk}")
    
    st.markdown("---")
    
    # 第二區：產品與規格 (對帳前置)
    cp1, cp2, cp3 = st.columns(3)
    d_prod = cp1.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = cp2.text_input("規格", key=f"sp_{rk}")
    d_content = cp3.text_input("使用產品內容(含預購）", key=f"cn_{rk}")

    st.markdown("---")

    # 第三區：批價內容與【精準對帳邏輯】
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    d_pre_total = 0
    d_pre_today = 0
    d_qty = 1
    can_submit = True 

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=10, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
    elif d_price == "使用前次預購":
        if not d_pid:
            st.warning("👈 請輸入病例 ID")
            can_submit = False
        else:
            df_history = fetch_all_data()
            if not df_history.empty:
                # 【邏輯修正】：精確計算該 ID 特定產品的預購餘額
                # 1. 取得該病人該產品的所有原始預購總量 (來自 "批價+預購" 或 "純預購寄庫")
                user_record = df_history[(df_history['病例號/ID'] == d_pid) & (df_history['產品項目'] == d_prod)]
                
                # 計算總預購量 (排除本身就是扣除紀錄的筆數)
                total_pre = pd.to_numeric(user_record['預購總量'], errors='coerce').sum()
                
                # 計算已扣除總量 (所有當日批價量的總和)
                total_used = pd.to_numeric(user_record['當日批價量'], errors='coerce').sum()
                
                current_balance = total_pre - total_used
                
                if current_balance > 0:
                    st.success(f"✅ {d_prod} 餘額：{int(current_balance)}")
                    d_pre_today = c5.number_input(f"扣除量 (餘:{int(current_balance)})", min_value=1, max_value=int(current_balance), value=1, key=f"py_{rk}")
                    d_qty = d_pre_today
                    c6.info(f"即將扣除：{d_pre_today}")
                else:
                    st.error(f"❌ {d_prod} 餘額不足")
                    can_submit = False
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=10, key=f"pt_{rk}")
        d_qty = 0

    d_pre_remain = d_pre_total - d_pre_today
    
    st.markdown("---")

    # 第四區：其餘資訊
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pname = c11.text_input("病人名", key=f"pn_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術名稱/使用部位", key=f"op_{rk}")
    d_loc = c14.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    with c17:
        d_memo = st.text_area("備註", key=f"me_{rk}", height=40, placeholder="備註...", label_visibility="collapsed")
    with c18:
        if st.button("🚀 提交數據", key="submit_btn", disabled=not can_submit):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    # 寫入正確數值到試算表
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, d_pre_remain, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.toast("✅ 已存檔")
                    time.sleep(1)
                    st.session_state.rk_v12 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except: st.error("存檔失敗")

with tab2:
    df_h = fetch_all_data()
    if not df_h.empty:
        st.dataframe(df_h.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    df_all = fetch_all_data()
    if not df_all.empty:
        # 僅顯示還有餘額的病人紀錄
        df_all['預購餘量'] = pd.to_numeric(df_all['預購餘量'], errors='coerce').fillna(0)
        df_pre = df_all[df_all['預購餘量'] > 0]
        st.dataframe(df_pre.iloc[::-1], use_container_width=True, hide_index=True)
