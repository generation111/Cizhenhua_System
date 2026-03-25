import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "01_跟刀紀錄管理"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

# 設定佈局為 wide，便於控制側邊欄
st.set_page_config(page_title=SYS_TITLE, layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式精修 (徹底解決對齊、框線凌亂，並縮減側邊欄) ---
st.markdown(f"""
<style>
    /* 隱藏預設 Header，僅保留 Tabs */
    [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; }}
    
    /* 縮減側邊欄寬度約 25% */
    [data-testid="stSidebar"] {{
        min-width: 220px !important;
        max-width: 220px !important;
    }}
    
    /* 主容器樣式 */
    .block-container {{ 
        padding-top: 3.5rem !important; 
        max-width: 950px !important; /* 配合 wide 佈局微調主區塊寬度 */
        background-color: #F0F9F0 !important; 
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    
    /* 系統標題樣式 */
    .sys-title {{ 
        text-align: center; font-size: 32px !important; font-weight: 900; color: #1e3a8a; 
        margin-top: -20px !important; margin-bottom: 25px !important; 
    }}
    
    /* 欄位標籤樣式 */
    [data-testid="stWidgetLabel"] p {{ 
        font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; 
        margin-bottom: 4px !important; 
    }}

    /* --- 核心：統一 43px 高度與單一邊框控制 (徹底解決凌亂) --- */
    /* 針對所有輸入框、下拉選單的外殼進行單一邊框定義，並移除內層重複線 */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {{
        height: 43px !important;
        min-height: 43px !important;
        background-color: white !important;
        border: 2px solid #1e3a8a !important; /* 單一加粗邊框 */
        border-radius: 8px !important;
        box-shadow: none !important;
    }}

    /* 解決 Selectbox (下拉選單) 內部結構的重複框線 */
    div[data-baseweb="select"] > div {{
        border: 2px solid #1e3a8a !important;
    }}
    
    /* 修正文字輸入欄位的內距與邊框 */
    input {{ 
        height: 41px !important; 
        line-height: 41px !important; 
        padding: 0 12px !important; 
        border: none !important; /* 移除內部重複線 */
    }}

    /* 備註欄 (TextArea) 特化控制，確保單一邊框且齊平 */
    .stTextArea textarea {{
        height: 43px !important;
        min-height: 43px !important;
        padding: 8px 12px !important;
        line-height: 1.3 !important;
        border: 2px solid #1e3a8a !important; /* 單一邊框 */
        border-radius: 8px !important;
        resize: none !important; /* 禁止拉動 */
    }}

    /* Tabs 標籤頁樣式 */
    .stTabs [data-baseweb="tab"] {{ 
        height: 52px !important; 
        font-weight: 800 !important; 
        font-size: 1.2rem !important;
    }}
    .stTabs [aria-selected="true"] {{ 
        background-color: #1e3a8a !important; 
        color: white !important; 
    }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 3. 數據核心 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except Exception: return None

ss = get_ss()

@st.cache_data(ttl=5)
def fetch_all_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            # 數值型態轉換
            num_cols = ['預購總量', '當日批價量', '預購餘量', '數量']
            for col in num_cols:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

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
    except Exception: return {"price":["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], "hosp":[], "dept":[], "prod":["3E PRP"], "rep":["Eric", "林國慈", "曾子榮"]}

OPT = get_options()

# --- 4. 介面佈局 ---
# 側邊欄內容
with st.sidebar:
    st.markdown("### 導航菜單")
    st.write("Home")
    st.write("**> 01_跟刀紀錄管理**")
    st.write("02_報表管理系統")

# 主介面
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_final_ui_fix" not in st.session_state: st.session_state.rk_final_ui_fix = 0
    rk = st.session_state.rk_final_ui_fix
    status_container = st.empty()
    db_df = fetch_all_data()

    # 第一列：批價內容 (1欄，因為日期改預設)
    c1, _ = st.columns([1, 1])
    d_price = c1.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}")
    
    # 第二列：醫師與產品 (3欄)
    c2, c3, c4 = st.columns(3)
    d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}")
    d_prod = c3.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}")
    d_dept = c4.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}")

    # 第三列：規格、ID、病人 (3欄)
    c5, c6, c7 = st.columns(3)
    d_spec = c5.text_input("規格", key=f"sp_{rk}")
    d_pid = c6.text_input("病例號/ID", key=f"pi_{rk}")
    d_pname = c7.text_input("病人名", key=f"pn_{rk}")
    
    # --- 預購邏輯計算區 (不帶雜線，對齊完美) ---
    c8, c9, c10 = st.columns(3)
    d_qty, d_pre_total, d_pre_today, can_submit = 0, 0, 0, True
    
    if d_price == "使用前次預購":
        p_now_id = st.session_state.get(f"pi_{rk}", "").strip()
        p_now_prod = st.session_state.get(f"pd_{rk}", "")
        
        # 抓取該 病例號+產品 的最後一筆餘額
        if p_now_id and p_now_prod and not db_df.empty:
            res_df = db_df[(db_df['病例號/ID'].astype(str).str.strip() == p_now_id) & (db_df['產品項目'] == p_now_prod)]
            cur_bal = int(res_df.iloc[-1]['預購餘量']) if not res_df.empty else 0
            
            if cur_bal > 0:
                c8.success(f"目前餘量：{cur_bal}")
                d_pre_today = c9.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}"); d_qty = d_pre_today
            else:
                c8.warning("⚠️ 餘額不足"); can_submit = False
        else:
            c8.info("請先輸入病例號與產品"); can_submit = False
            
    elif d_price == "批價 + 預購":
        d_pre_total = c8.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c9.number_input("當日批價量", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    else:
        d_qty = c8.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty

    # 第四列：手術與地點 (3欄)
    c11, c12, c13 = st.columns(3)
    d_op = c11.text_input("手術名稱/部位", key=f"op_{rk}")
    d_loc = c12.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}")
    d_hosp = c13.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}")

    # 第五列：人員與備註 (提交按鈕對齊區)
    c14, c15, c16 = st.columns(3)
    d_blood = c14.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}")
    d_rep = c15.selectbox("跟刀(操作)人員", OPT.get("rep"), key=f"rp_{rk}")
    d_memo = c16.text_area("備註", key=f"me_{rk}")
    
    with c16: # 提交按鈕與備註齊平
        st.write("") # 對齊補償
        if st.button("🚀 提交數據", key="sub_btn", disabled=not (can_submit and d_pid), use_container_width=True):
            with st.spinner("存檔中..."):
                # 再次校準預購餘量
                latest_df = fetch_all_data()
                prev_res = latest_df[(latest_df['病例號/ID'].astype(str).str.strip() == d_pid.strip()) & (latest_df['產品項目'] == d_prod)]
                curr_bal = int(prev_res.iloc[-1]['預購餘量']) if not prev_res.empty else 0
                
                # 計算最終餘額
                if d_price == "使用前次預購": final_bal = curr_bal - d_pre_today
                elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal = curr_bal + (d_pre_total - d_pre_today)
                else: final_bal = 0
                
                # 對齊試算表欄位順序寫入 (假設 19 欄結構)
                now_dt = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
                row = [now_dt, d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, final_bal, "", d_pname, d_pid, d_op, d_loc, d_blood, d_rep, d_memo]
                
                try:
                    ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
                    status_container.success("✅ 存檔成功！已記錄資料線。")
                    st.cache_data.clear() # 清除緩存以讀取最新資料
                    time.sleep(1); st.session_state.rk_final_ui_fix += 1; st.rerun()
                except:
                    status_container.error("提交失敗，請檢查網路。")

with tab2:
    st.write("### 📊 最近 50 筆紀錄")
    hist_df = fetch_all_data()
    if not hist_df.empty:
        st.dataframe(hist_df.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    st.write("### 🔍 剩餘預購名單")
    track_df = fetch_all_data()
    if not track_df.empty:
        # 篩選預購餘量大於 0 的組
        res = track_df.groupby(['病例號/ID', '產品項目']).tail(1)
        display_df = res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']]
        if not display_df.empty:
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.write("目前無剩餘預購。")
