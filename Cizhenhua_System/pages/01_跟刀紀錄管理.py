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

# --- 2. 樣式優化 (4.5rem 確保標題不被切割) ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 6rem !important; padding-bottom: 0.2rem !important; }}
    .sys-title {{ 
        text-align: center; 
        font-size: 26px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -45px !important; 
        margin-bottom: 25px !important;
        white-space: nowrap; 
    }}
    hr {{ border: 0.5px solid #f0f2f6 !important; margin: 10px 0 !important; }}
    div[data-testid="column"] {{ display: flex; align-items: center; justify-content: center; }}
    div[data-testid="stTextArea"] label {{ display: none !important; }}
    div[data-testid="stTextArea"] textarea {{ height: 40px !important; min-height: 40px !important; padding: 8px !important; }}
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
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 基本資料
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容(含預購）", key=f"cn_{rk}")
    
    # 核心邏輯
    st.markdown("---")
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    # 邏輯分流與數值初始化
    d_pre_total = 0
    d_pre_today = 0
    d_qty = 1

    if d_price == "單次批價使用":
        st.caption("✅ 模式：單次直接批價。")
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
        c6.info(f"當日批價量：{d_pre_today}")

    elif d_price == "批價 + 預購":
        st.caption("✅ 模式：當日使用並預購。")
        d_pre_total = c5.number_input("預購總量", min_value=1, value=10, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today

    elif d_price == "使用前次預購":
        st.warning("⚠️ 模式：扣除前次寄庫。")
        d_pre_today = c5.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
        c6.info(f"扣除量：{d_pre_today}")

    elif d_price == "使用他人預購":
        st.error("❗ 模式：跨人扣帳（請於備註註明）。")
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
        c6.info(f"扣除量：{d_pre_today}")

    elif d_price == "純預購寄庫":
        st.caption("✅ 模式：純寄庫不批價。")
        d_pre_total = c5.number_input("預購總量", min_value=1, value=10, key=f"pt_{rk}")
        d_qty = 0
        c6.success(f"寄庫：{d_pre_total}")

    # 即時餘量計算與位置調整 (紅框修正)
    d_pre_remain = d_pre_total - d_pre_today
    if d_pre_remain > 0:
        # 當有正數餘量時，在右側空白區塊下方顯示提示
        with c6:
            st.markdown(f"💡 **即時餘量：{d_pre_remain}**")
    
    st.markdown("---")

    # 其他輸入欄位
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")
    
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術名稱/使用部位", key=f"op_{rk}")
    d_loc = c14.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    d_memo = c17.text_area("備註", key=f"me_{rk}", height=40, placeholder="備註...", label_visibility="collapsed")
    
    with c18:
        if st.button("🚀 提交數據", key="submit_btn"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    row = [
                        str(d_date), d_price, d_hosp, d_dept, d_dr, 
                        d_prod, d_spec, d_qty, d_pre_total, d_pre_today, d_pre_remain, 
                        d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo
                    ]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.toast(f"✅ 存檔成功！")
                    time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except Exception as e: st.error(f"寫入失敗: {e}")

# 歷史與預購分頁維持原邏輯
with tab2:
    df_h = fetch_all_data()
    if not df_h.empty:
        st.dataframe(df_h.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    df_all = fetch_all_data()
    if not df_all.empty and '預購餘量' in df_all.columns:
        df_all['預購餘量'] = pd.to_numeric(df_all['預購餘量'], errors='coerce').fillna(0)
        df_pre = df_all[df_all['預購餘量'] > 0]
        st.dataframe(df_pre.iloc[::-1], use_container_width=True, hide_index=True)
