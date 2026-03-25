import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time
import streamlit.components.v1 as components

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "01_跟刀紀錄管理"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=SYS_TITLE, layout="wide", initial_sidebar_state="collapsed")

# --- 2. 手勢滑動 JS 注入 (核心功能) ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    let touchstartX = 0;
    let touchendX = 0;

    function handleGesture() {
        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
        let activeTabIndex = -1;
        tabs.forEach((tab, index) => {
            if (tab.getAttribute('aria-selected') === 'true') activeTabIndex = index;
        });

        if (touchendX < touchstartX - 100) { // 向左滑 -> 下一個 Tab
            if (activeTabIndex < tabs.length - 1) tabs[activeTabIndex + 1].click();
        }
        if (touchendX > touchstartX + 100) { // 向右滑 -> 上一個 Tab
            if (activeTabIndex > 0) tabs[activeTabIndex - 1].click();
        }
    }

    doc.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, false);
    doc.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleGesture(); }, false);
    </script>
    """,
    height=0,
)

# --- 3. 樣式精修 (維持 43px、單一邊框、4rem) ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ background-color: #F0F9F0 !important; }}
    [data-testid="stSidebar"] {{ min-width: 220px !important; max-width: 220px !important; }}
    
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

    /* --- 徹底解決重複框線 --- */
    div[data-baseweb="input"], div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"], .stTextArea textarea {{
        border: none !important; box-shadow: none !important; background-color: transparent !important;
    }}

    div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div, 
    div[data-testid="stNumberInput"] > div, div[data-testid="stTextArea"] > div {{
        height: 43px !important;
        border: 2px solid #1e3a8a !important; 
        border-radius: 8px !important;
        background-color: white !important;
        overflow: hidden !important;
    }}

    input {{ height: 41px !important; padding: 0 12px !important; line-height: 41px !important; }}
    .stTextArea textarea {{ height: 39px !important; padding: 8px 12px !important; line-height: 1.2 !important; }}

    .stTabs [data-baseweb="tab"] {{ height: 50px !important; font-weight: 800 !important; font-size: 1.1rem !important; }}
    .stTabs [aria-selected="true"] {{ background-color: #1e3a8a !important; color: white !important; border-radius: 8px 8px 0 0; }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 4. 數據核心 (完整不省略) ---
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
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            for col in ['預購總量', '當日批價量', '預購餘量', '數量']:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
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
    except: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購"], "hosp":[], "dept":[], "prod":["3E PRP"], "rep":["Eric"]}

OPT = get_options()

# --- 5. 介面佈局 ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "full_v8_key" not in st.session_state: st.session_state.full_v8_key = 0
    rk = st.session_state.full_v8_key
    db_df = fetch_all_data()

    # 第一列
    c1, c2 = st.columns(2)
    d_price = c1.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_hosp = c2.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    
    # 第二列
    c3, c4, c5 = st.columns(3)
    d_dr = c3.text_input("醫師姓名", key=f"dr_{rk}")
    d_prod = c4.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_dept = c5.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")

    # 第三列
    c6, c7, c8 = st.columns(3)
    d_spec = c6.text_input("規格", key=f"sp_{rk}")
    d_pid = c7.text_input("病例號/ID", key=f"pi_{rk}")
    d_pname = c8.text_input("病人名", key=f"pn_{rk}")
    
    # 第四列：數量邏輯區
    c9, c10, c11 = st.columns(3)
    d_qty, d_pre_total, d_pre_today, can_sub = 0, 0, 0, True
    
    if d_price == "使用前次預購":
        curr_id = st.session_state.get(f"pi_{rk}", "").strip()
        curr_pd = st.session_state.get(f"pd_{rk}", "")
        u_df = db_df[(db_df['病例號/ID'].astype(str).str.strip() == curr_id) & (db_df['產品項目'] == curr_pd)]
        bal = int(u_df.iloc[-1]['預購餘量']) if not u_df.empty else 0
        if bal > 0:
            c9.success(f"目前餘量：{bal}")
            d_pre_today = c10.number_input("扣除量", min_value=1, max_value=bal, value=1, key=f"py_{rk}"); d_qty = d_pre_today
        else:
            c9.warning("⚠️ 無預購餘量"); can_sub = False
    elif d_price == "批價 + 預購":
        d_pre_total = c9.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c10.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    else:
        d_qty = c9.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty
    
    d_content = c11.text_input("產品內容(含預購)", key=f"cn_{rk}")

    # 第五列
    c12, c13, c14 = st.columns(3)
    d_op = c12.text_input("手術名稱/部位", key=f"op_{rk}")
    d_loc = c13.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_blood = c14.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")

    # 第六列
    c15, c16, c17 = st.columns(3)
    d_rep = c15.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    d_memo = c16.text_area("備註", key=f"me_{rk}")
    
    with c17:
        st.write("") # 垂直對齊
        if st.button("🚀 提交數據", use_container_width=True, disabled=not (can_sub and d_pid)):
            now_dt = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
            # 計算寫入餘量
            tmp_df = fetch_all_data()
            prev_res = tmp_df[(tmp_df['病例號/ID'].astype(str).str.strip() == d_pid.strip()) & (tmp_df['產品項目'] == d_prod)]
            curr_bal = int(prev_res.iloc[-1]['預購餘量']) if not prev_res.empty else 0
            
            if d_price == "使用前次預購": final_bal = curr_bal - d_pre_today
            elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal = curr_bal + (d_pre_total - d_pre_today)
            else: final_bal = 0
            
            row = [now_dt, d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, final_bal, d_content, d_pname, d_pid, d_op, d_loc, d_blood, d_rep, d_memo]
            ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
            st.toast("✅ 存檔成功！")
            st.cache_data.clear()
            time.sleep(1); st.session_state.full_v8_key += 1; st.rerun()

with tab2:
    st.write("### 📊 最近 50 筆紀錄")
    h_df = fetch_all_data()
    if not h_df.empty:
        st.dataframe(h_df.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    st.write("### 🔍 剩餘預購名單")
    t_df = fetch_all_data()
    if not t_df.empty:
        res = t_df.groupby(['病例號/ID', '產品項目']).tail(1)
        st.dataframe(res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']], use_container_width=True, hide_index=True)
