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

# --- 2. 手勢滑動 JS 注入 (核心功能復原) ---
# 這段代碼會監聽手指滑動，並自動點擊 Streamlit 的 Tab 按鈕
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

# --- 3. 樣式精修 (維持 43px、單一框線、4rem) ---
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

    /* 單一框線與高度控制 */
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
    .stTextArea textarea {{ height: 39px !important; padding: 8px 12px !important; }}

    .stTabs [data-baseweb="tab"] {{ height: 50px !important; font-weight: 800 !important; font-size: 1.1rem !important; }}
    .stTabs [aria-selected="true"] {{ background-color: #1e3a8a !important; color: white !important; border-radius: 8px 8px 0 0; }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 4. 數據核心 (省略部分重複邏輯以求精簡) ---
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
        for col in ['預購總量', '當日批價量', '預購餘量', '數量']:
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
    except: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購"], "hosp":[], "dept":[], "prod":["3E PRP"], "rep":["Eric"]}

OPT = get_options()

# --- 5. 介面與提交邏輯 ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_gesture_v1" not in st.session_state: st.session_state.rk_gesture_v1 = 0
    rk = st.session_state.rk_gesture_v1
    db_df = fetch_all_data()

    # (此處放置之前的錄入表單 columns 佈局...)
    c1, c2 = st.columns(2)
    d_price = c1.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    d_hosp = c2.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")
    
    c3, c4, c5 = st.columns(3)
    d_dr = c3.text_input("醫師姓名", key=f"dr_{rk}")
    d_prod = c4.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_pid = c5.text_input("病例號/ID", key=f"pi_{rk}")

    # (省略中間其餘欄位，邏輯與前版一致)
    if st.button("🚀 提交數據", use_container_width=True):
        # 存檔邏輯...
        st.toast("✅ 已提交")
        time.sleep(1); st.session_state.rk_gesture_v1 += 1; st.rerun()

with tab2: st.dataframe(fetch_all_data().iloc[::-1].head(50), use_container_width=True)
with tab3: st.write("預購追蹤區")
