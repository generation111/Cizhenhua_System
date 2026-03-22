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

# --- 2. 樣式優化 (完全採用佰哥手動調整之參數) ---
st.markdown(f"""
<style>
    /* 1. 調整整體頁面間距 (佰哥調校版) */
    .block-container {{ padding-top: 5rem !important; padding-bottom: 0.2rem !important; }}
    
    /* 2. 調整標題位置與下方間距 (佰哥調校版) */
    .sys-title {{ 
        text-align: center; 
        font-size: 26px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -30px !important; 
        margin-bottom: 5px !important; 
        white-space: nowrap; 
    }}
    
    /* 極窄分隔線 */
    hr {{ 
        border: 0 !important; 
        border-top: 1px solid #e6e9ef !important; 
        margin: 5px 0 !important; 
        padding: 0 !important;
    }}
    
    /* 調整元件間預設間距 */
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
    except:
        return None

ss = get_ss()

@st.cache_data(ttl=10)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            # 確保數值轉型容錯
            num_cols = ['預購總量', '當日批價量', '預購餘量']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].replace('', '0'), errors='coerce').fillna(0)
            return df
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

# --- 4. 核心餘額計算邏輯 ---
def get_current_balance(df, pid, prod):
    if df.empty or not pid: return 0
    u_rec = df[(df['病例號/ID'].astype(str) == str(pid)) & (df['產品項目'] == prod)]
    # 總寄庫 = 批價+預購(預購總量) + 純預購(預購總量)
    total_in = u_rec[u_rec['批價內容'].isin(['批價 + 預購', '純預購寄庫'])]['預購總量'].sum()
    # 總消耗 = 批價+預購(當日量) + 使用前次(當日量) + 使用他人(當日量)
    total_out = u_rec[u_rec['批價內容'].isin(['批價 + 預購', '使用前次預購', '使用他人預購'])]['當日批價量'].sum()
    return int(total_in - total_out)

# --- 5. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v20" not in st.session_state: st.session_state.rk_v20 = 0
    rk = st.session_state.rk_v20
    
    # 用於顯示提交結果的空容器
    msg_container = st.empty()
    
    # 作業區塊 1：基礎資料 (完全恢復原順序與欄位)
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容(含預購）", key=f"cn_{rk}")
    
    st.markdown("---")
    
    # 作業區塊 2：批價內容 (恢復原順序、大小與防呆提示位置)
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    d_pre_total, d_pre_today, d_qty = 0, 0, 0
    current_balance = 0
    can_submit = True
    
    # 先抓取資料庫供對帳使用
    db_df = fetch_all_data()

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
        c6.info(f"當日批價量：{d_pre_today}")
        
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
        
    elif d_price == "使用前次預購":
        d_pid_check = st.session_state.get(f"pi_{rk}", "").strip() # 獲取下方 ID 欄位值
        d_prod_check = st.session_state.get(f"pd_{rk}", "") # 獲取下方產品欄位值
        
        if not d_pid_check:
            c5.warning("👈 請輸入 ID (下方)")
            can_submit = False
        else:
            current_balance = get_current_balance(db_df, d_pid_check, d_prod_check)
            if current_balance > 0:
                c6.success(f"✅ 累計餘量：{current_balance}")
                d_pre_today = c5.number_input("扣除量", min_value=1, max_value=current_balance, value=1, key=f"py_{rk}")
                d_qty = d_pre_today
            else:
                c6.error("❌ 餘額為 0")
                can_submit = False
                
    elif d_price == "使用他人預購":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
        d_pre_today = d_qty
        c6.info(f"借用量：{d_pre_today}")
        
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        c6.success(f"寄庫：{d_pre_total}")
        d_qty = 0

    st.markdown("---")

    # 作業區塊 3：產品細節 (完全恢復原佈局)
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")
    
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}") # 這裡輸入 ID 後會觸發上方邏輯
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術名稱/使用部位", key=f"op_{rk}")
    d_loc = c14.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    
    # 恢復原備註與按鈕位置
    with c17:
        d_memo = st.text_area("備註", key=f"me_{rk}", height=40, placeholder="備註內容...", label_visibility="collapsed")
    with c18:
        if st.button("🚀 提交數據", key="submit_btn", disabled=not can_submit):
            with st.spinner("存檔中..."):
                try:
                    # 遞扣寫入邏輯
                    latest_df = fetch_all_data()
                    real_bal = get_current_balance(latest_df, d_pid, d_prod)
                    
                    if d_price == "單次批價使用": remain = 0
                    elif d_price == "使用前次預購": remain = real_bal - d_pre_today
                    elif d_price in ["批價 + 預購", "純預購寄庫"]: remain = real_bal + d_pre_total - d_pre_today
                    else: remain = 0
                    
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, remain, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    
                    msg_container.success("✅ 存檔成功，餘額已遞扣")
                    time.sleep(1)
                    st.session_state.rk_v20 += 1
                    st.cache_data.clear() 
                    st.rerun()
                except: msg_container.error("提交失敗")

# 歷史紀錄與追蹤分頁恢復原樣
with tab2:
    df_h = fetch_all_data()
    if not df_h.empty:
        st.dataframe(df_h.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    df_all = fetch_all_data()
    if not df_all.empty:
        summary = df_all.groupby(['病例號/ID', '產品項目']).apply(
            lambda x: get_current_balance(df_all, x.name[0], x.name[1])
        ).reset_index(name='剩餘總量')
        st.dataframe(summary[summary['剩餘總量'] > 0], use_container_width=True, hide_index=True)
