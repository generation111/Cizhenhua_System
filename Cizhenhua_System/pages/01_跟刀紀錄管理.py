import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time
import streamlit.components.v1 as components

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（清晰大字護眼版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 樣式強化 (佰哥調校：大字號 + 統一高度 + 框線 + 護眼綠) ---
st.markdown(f"""
<style>
    /* 1. 頁面間距與護眼背景 */
    .block-container {{ 
        padding-top: 3.3rem !important; 
        padding-bottom: 0.2rem !important; 
        background-color: #F0F9F0 !important; /* 護眼蘋果綠 */
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}

    /* 2. 標題大字強化 */
    .sys-title {{ 
        text-align: center; font-size: 30px !important; font-weight: 900; color: #1e3a8a; 
        margin-top: -15px !important; margin-bottom: 12px !important; 
    }}
    
    /* 3. 所有標籤 (Labels) 加大與加粗 */
    [data-testid="stWidgetLabel"] p {{
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }}

    /* 4. 【核心修正】錄入框統一高度與樣式 */
    /* 文字框、數字框、日期框 */
    .stTextInput input, .stNumberInput input, .stDateInput input {{
        height: 48px !important; /* 統一高度 */
        border: 1px solid #1e3a8a !important;
        border-radius: 8px !important;
        padding: 0 10px !important; /* 調整內距確保文字置中 */
        background-color: white !important;
        font-size: 1.1rem !important;
    }}
    
    /* 下拉選單 (Selectbox) 的外層與內層高度統一 */
    .stSelectbox [data-baseweb="select"] {{
        height: 48px !important; /* 統一高度 */
        border: 1px solid #1e3a8a !important;
        border-radius: 8px !important;
        background-color: white !important;
        display: flex;
        align-items: center; /* 內部文字垂直置中 */
    }}
    
    /* 下拉選單內部文字樣式修正 */
    .stSelectbox [data-baseweb="select"] > div {{
        height: 48px !important;
        display: flex;
        align-items: center;
        padding-left: 10px !important;
        font-size: 1.1rem !important;
    }}

    /* 錄入框點擊時的特效 */
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox [data-baseweb="select"]:focus-within {{
        border: 2px solid #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
    }}

    /* 5. 分頁標籤 (Tabs) */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background-color: rgba(255,255,255,0.5); padding: 5px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 48px; background-color: white; border-radius: 8px; 
        color: #64748b; font-weight: 700; border: 1px solid #e2e8f0;
        font-size: 1.1rem !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1e3a8a !important; color: white !important;
    }}

    /* 6. 按鈕樣式 (微調高度) */
    div.stButton > button {{ 
        height: 50px !important; width: 100% !important; font-weight: bold !important; font-size: 1.2rem !important;
        background-color: #1e3a8a !important; color: white !important; border-radius: 8px !important;
    }}
    
    hr {{ border: 0 !important; border-top: 2px solid #cbd5e1 !important; margin: 10px 0 !important; }}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- 3. 加入手勢滑動偵測 (JavaScript) ---
components.html("""
<script>
    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
    let touchstartX = 0; let touchendX = 0;
    function handleGesture() {
        const activeTab = Array.from(tabs).findIndex(t => t.getAttribute('aria-selected') === 'true');
        if (touchendX < touchstartX - 70) { if (activeTab < tabs.length - 1) tabs[activeTab + 1].click(); }
        if (touchendX > touchstartX + 70) { if (activeTab > 0) tabs[activeTab - 1].click(); }
    }
    window.parent.document.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; });
    window.parent.document.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleGesture(); });
</script>
""", height=0)

# --- 4. 數據核心 (保持不變) ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
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
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            df['病例號/ID'] = df['病例號/ID'].astype(str).str.strip()
            df['產品項目'] = df['產品項目'].astype(str).str.strip()
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_current_balance(df, pid, prod):
    if df.empty or not pid: return 0
    u_rec = df[(df['病例號/ID'] == str(pid)) & (df['產品項目'] == prod)]
    total_in = pd.to_numeric(u_rec[u_rec['批價內容'].isin(['批價 + 預購', '純預購寄庫'])]['預購總量'], errors='coerce').sum()
    total_out = pd.to_numeric(u_rec[u_rec['批價內容'].isin(['批價 + 預購', '使用前次預購', '使用他人預購'])]['當日批價量'], errors='coerce').sum()
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
    except: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], "hosp":[], "dept":[], "prod":["3E PRP"], "loc":[], "blood":[], "rep":[]}

OPT = get_options()

# --- 5. 介面 (維持佰哥佈局，統一錄入框高度) ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v25" not in st.session_state: st.session_state.rk_v25 = 0
    rk = st.session_state.rk_v25
    status_msg = st.empty()
    
    # 區塊 1
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容(含預購）", key=f"cn_{rk}")
    st.markdown("---")
    
    # 作業區塊 2
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_pre_total, d_pre_today, d_qty, can_submit = 0, 0, 0, True
    db_df = fetch_all_data()

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    elif d_price == "使用前次預購":
        p_now, pr_now = st.session_state.get(f"pi_{rk}", "").strip(), st.session_state.get(f"pd_{rk}", "")
        cur_bal = get_current_balance(db_df, p_now, pr_now)
        if cur_bal > 0:
            c6.success(f"✅ PRP 餘量：{cur_bal}")
            d_pre_today = c5.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}"); d_qty = d_pre_today
        else:
            c5.warning("請輸入 ID 或餘額不足"); can_submit = False
    elif d_price == "使用他人預購":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}"); d_qty = 0

    st.markdown("---")

    # 作業區塊 3 (產品資料)
    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")
    
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術名稱/部位", key=f"op_{rk}")
    d_loc = c14.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    
    with c17: d_memo = st.text_area("備註", key=f"me_{rk}", height=45, label_visibility="collapsed")
    with c18:
        if st.button("🚀 提交錄入數據", key="sub_btn", disabled=not can_submit):
            try:
                now_df = fetch_all_data()
                now_bal = get_current_balance(now_df, d_pid, d_prod)
                if d_price == "使用前次預購": remain = now_bal - d_pre_today
                elif d_price in ["批價 + 預購", "純預購寄庫"]: remain = now_bal + d_pre_total - d_pre_today
                else: remain = 0
                row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, remain, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
                status_msg.success("✅ 資料已成功存檔！"); time.sleep(1); st.cache_data.clear(); st.session_state.rk_v25 += 1; st.rerun()
            except: status_msg.error("提交異常")

# tab2 & tab3 維持原樣...
with tab2:
    st.write("### 📋 最近 50 筆錄入紀錄")
    df_h = fetch_all_data()
    if not df_h.empty: st.dataframe(df_h.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    st.write("### 🔍 全院 PRP 預購餘量追蹤")
    df_all = fetch_all_data()
    if not df_all.empty:
        summary = df_all.groupby(['病例號/ID', '產品項目']).apply(lambda x: get_current_balance(df_all, x.name[0], x.name[1])).reset_index(name='剩餘總量')
        st.dataframe(summary[summary['剩餘總量'] > 0], use_container_width=True, hide_index=True)
