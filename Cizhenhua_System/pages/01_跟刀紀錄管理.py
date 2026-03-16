import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "2026 年度跟刀紀錄管理系統"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 (標題縮緊 + 移除分隔線 + 單列對齊) ---
st.markdown("""
<style>
    /* 1. 標題區塊上下空白極致縮減 */
    .block-container { 
        padding-top: 3em !important; 
        padding-bottom: 0rem !important; 
    }
    .sys-title { 
        text-align: center; 
        font-size: 26px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -10px !important;
        margin-bottom: 15px !important;
    }

    /* 2. 移除所有分隔線與多餘外距 */
    hr { display: none !important; }
    .stTabs [data-baseweb="tab-list"] { margin-bottom: 10px !important; }
    
    /* 3. 底欄單列對齊設定 */
    /* 讓 column 內的物件垂直置中 */
    div[data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* 隱藏備註輸入框的預設 Label */
    div[data-testid="stTextArea"] label { display: none !important; }
    
    /* 強制輸入框高度與按鈕一致 (40px) */
    div[data-testid="stTextArea"] textarea {
        height: 40px !important;
        min-height: 40px !important;
        padding: 8px !important;
        border-radius: 5px !important;
    }

    /* 按鈕樣式 (40px) */
    div.stButton > button {
        height: 40px !important;
        width: 100% !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border: 2px solid #1E3A8A !important;
        color: #1E3A8A !important;
        background-color: #FFF !important;
        border-radius: 5px !important;
        transition: 0.3s;
    }
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

@st.cache_data(ttl=10)
def get_options():
    """從 Settings 工作表抓取所有選單"""
    if not ss: return {}, []
    try:
        ws = ss.worksheet("Settings")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        
        # 動態對應
        opts = {
            "price": [x for x in df["批價內容"].dropna().unique() if x],
            "hosp": [x for x in df["使用醫院"].dropna().unique() if x],
            "dept": [x for x in df["使用科別"].dropna().unique() if x],
            "prod": [x for x in df["產品項目"].dropna().unique() if x],
            "loc": [x for x in df["使用地點"].dropna().unique() if x],
            "blood": [x for x in df["抽血人員"].dropna().unique() if x],
            "rep": [x for x in df["跟刀(操作)人員"].dropna().unique() if x]
        }
        return opts
    except:
        return {}, []

# 讀取選單
OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 第一排
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}")
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_content = c3.text_input("使用產品內容-含預購", key=f"cn_{rk}")
    
    # 第二排
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", OPT.get("price", ["載入中"]), key=f"pr_{rk}")
    d_prod = c5.selectbox("產品項目", OPT.get("prod", ["載入中"]), key=f"pd_{rk}")
    d_pname = c6.text_input("病人名", key=f"pn_{rk}")
    
    # 第三排
    c7, c8, c9 = st.columns(3)
    d_hosp = c7.selectbox("使用醫院", OPT.get("hosp", ["載入中"]), key=f"hs_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pid = c9.text_input("病例號/ID", key=f"pi_{rk}")
    
    # 第四排
    c10, c11, c12 = st.columns(3)
    d_dept = c10.selectbox("使用科別", OPT.get("dept", ["載入中"]), key=f"dp_{rk}")
    d_qty = c11.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")
    d_opname = c12.text_input("手術名稱/使用部位", key=f"op_{rk}")
    
    # 第五排
    c13, c14, c15 = st.columns(3)
    d_loc = c13.selectbox("使用地點", OPT.get("loc", ["血管攝影室", "開刀房"]), key=f"lc_{rk}")
    d_blood = c14.selectbox("抽血人員", OPT.get("blood", ["載入中"]), key=f"bl_{rk}")
    d_rep = c15.selectbox("跟刀(操作)人員", OPT.get("rep", ["載入中"]), key=f"rp_{rk}")

    # --- 關鍵修正：底欄單列無分隔線 ---
    # 分配比例：標籤(0.3), 輸入框(3.2), 按鈕(1)
    bc1, bc2, bc3 = st.columns([0.3, 3.2, 1])
    
    with bc1:
        st.markdown('<p style="font-weight:bold; margin-bottom:0px;">備註</p>', unsafe_allow_html=True)
    
    with bc2:
        d_memo = st.text_area("", key=f"me_{rk}", height=40, placeholder="請輸入備註...")
        
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            with st.spinner("存檔中..."):
                try:
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.cache_data.clear()
                    st.toast("✅ 資料已成功存檔"); time.sleep(1); st.session_state.rk_v11 += 1; st.rerun()
                except: st.error("寫入失敗")