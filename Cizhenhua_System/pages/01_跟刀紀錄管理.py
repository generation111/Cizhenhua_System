import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time
import streamlit.components.v1 as components

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（終極修復結構版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 樣式終極精修 (高度 42px + 字體加大 + 分頁強化) ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 3rem !important; background-color: #F0F9F0 !important; }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    .sys-title {{ text-align: center; font-size: 28px !important; font-weight: 900; color: #1e3a8a; margin-bottom: 15px !important; }}

    [data-testid="stWidgetLabel"] p {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 2px !important; }}

    /* 所有錄入框高度 42px & 字體加大 */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important;
        border: 1px solid #1e3a8a !important;
        border-radius: 8px !important;
        height: 42px !important;
        box-sizing: border-box !important;
    }}

    .stTextInput input, .stDateInput input, .stNumberInput input {{
        height: 40px !important;
        font-size: 1.2rem !important;
        font-weight: 500 !important;
        color: #1e293b !important;
        background-color: transparent !important;
        border: none !important;
    }}

    .stSelectbox [data-baseweb="select"] div {{ font-size: 1.2rem !important; font-weight: 500 !important; }}
    .stSelectbox [data-baseweb="select"] > div {{ height: 40px !important; display: flex; align-items: center; padding-left: 8px !important; }}

    .stTextArea textarea {{ height: 40px !important; min-height: 40px !important; font-size: 1.1rem !important; border: none !important; padding: 5px 10px !important; }}

    /* 分頁標籤強化加大 */
    .stTabs [data-baseweb="tab"] {{
        height: 52px !important;
        background-color: white; 
        border-radius: 8px 8px 0 0; 
        color: #64748b; 
        font-weight: 800 !important; 
        font-size: 1.25rem !important;
        border: 1px solid #e2e8f0;
        padding: 0 25px !important;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #1e3a8a !important; color: white !important; }}

    div.stButton > button {{ height: 48px !important; width: 100% !important; font-size: 1.2rem !important; font-weight: bold !important; background-color: #1e3a8a !important; color: white !important; }}

    hr {{ display: none !important; }}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動功能修復腳本 ---
components.html("""
<script>
    const doc = window.parent.document;
    let touchstartX = 0;
    let touchendX = 0;

    function handleGesture() {
        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
        if (!tabs || tabs.length === 0) return;
        
        let activeTabIndex = -1;
        tabs.forEach((tab, index) => {
            if (tab.getAttribute('aria-selected') === 'true') activeTabIndex = index;
        });

        const swipeDistance = touchendX - touchstartX;
        
        if (swipeDistance < -80) { // 向左滑 -> 下一頁
            if (activeTabIndex < tabs.length - 1) {
                tabs[activeTabIndex + 1].click();
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        }
        if (swipeDistance > 80) { // 向右滑 -> 上一頁
            if (activeTabIndex > 0) {
                tabs[activeTabIndex - 1].click();
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        }
    }

    doc.addEventListener('touchstart', e => {
        touchstartX = e.changedTouches[0].screenX;
    }, {passive: true});

    doc.addEventListener('touchend', e => {
        touchendX = e.changedTouches[0].screenX;
        handleGesture();
    }, {passive: true});
</script>
""", height=0)

# --- 4. 數據核心 ---
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

@st.cache_data(ttl=2)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            df['預購總量'] = pd.to_numeric(df['預購總量'], errors='coerce').fillna(0)
            df['當日批價量'] = pd.to_numeric(df['當日批價量'], errors='coerce').fillna(0)
            df['病例號/ID'] = df['病例號/ID'].astype(str).str.strip()
            df['產品項目'] = df['產品項目'].astype(str).str.strip()
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_current_balance(df, pid, prod):
    if df.empty or not pid or not prod: return 0
    user_df = df[(df['病例號/ID'] == str(pid)) & (df['產品項目'] == prod)]
    total_in = user_df[user_df['批價內容'].isin(['批價 + 預購', '純預購寄庫'])]['預購總量'].sum()
    total_out = user_df[user_df['批價內容'].isin(['批價 + 預購', '使用前次預購', '使用他人預購'])]['當日批價量'].sum()
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

# --- 5. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v33" not in st.session_state: st.session_state.rk_v33 = 0
    rk = st.session_state.rk_v33
    status_msg = st.empty()
    db_df = fetch_all_data()

    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容(含預購)", key=f"cn_{rk}")
    
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_pre_total, d_pre_today, d_qty, can_submit = 0, 0, 0, True

    if d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    elif d_price == "使用前次預購":
        p_now = st.session_state.get(f"pi_{rk}", "").strip()
        pr_now = st.session_state.get(f"pd_{rk}", "")
        cur_bal = get_current_balance(db_df, p_now, pr_now)
        if cur_bal > 0:
            c6.success(f"餘量：{cur_bal}")
            d_pre_today = c5.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}"); d_qty = d_pre_today
        else:
            c5.warning("餘額不足或無ID"); can_submit = False
    elif d_price == "使用他人預購":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty
    elif d_price == "純預購寄庫":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}"); d_qty = 0

    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")
    
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}")
    d_dept = c12.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")
    
    c13, c14, c15 = st.columns(3)
    d_opname = c13.text_input("手術/部位", key=f"op_{rk}")
    d_loc = c14.selectbox("地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("跟刀(操作)", OPT.get("rep"), key=f"rp_{rk}")
    with c17: d_memo = st.text_area("備註", key=f"me_{rk}")
    with c18:
        st.write("")
        if st.button("🚀 提交數據", key="sub_btn", disabled=not can_submit):
            try:
                final_bal = get_current_balance(db_df, d_pid, d_prod)
                if d_price == "使用前次預購": final_bal -= d_pre_today
                elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal += (d_pre_total - d_pre_today)
                else: final_bal = 0 if d_price == "單次批價使用" else final_bal - d_pre_today
                
                row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, final_bal, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
                status_msg.success("✅ 已存檔！")
                st.cache_data.clear()
                time.sleep(1); st.session_state.rk_v33 += 1; st.rerun()
            except: status_msg.error("提交異常")

with tab2:
    hist_df = fetch_all_data()
    if not hist_df.empty:
        st.dataframe(hist_df.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    tracking_df = fetch_all_data()
    if not tracking_df.empty:
        summary = tracking_df.groupby(['病例號/ID', '產品項目']).size().reset_index()
        summary['剩餘總量'] = summary.apply(lambda x: get_current_balance(tracking_df, x['病例號/ID'], x['產品項目']), axis=1)
        st.dataframe(summary[summary['剩餘總量'] > 0][['病例號/ID', '產品項目', '剩餘總量']], use_container_width=True, hide_index=True)
