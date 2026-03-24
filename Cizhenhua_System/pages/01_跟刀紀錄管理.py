import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time
import streamlit.components.v1 as components

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=SYS_TITLE, layout="centered", initial_sidebar_state="collapsed")

# --- 2. 介面精修 ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1rem !important; background-color: #F8FAFC !important; }}
    .sys-title {{ text-align: center; font-size: 26px; font-weight: 900; color: #1e3a8a; margin-bottom: 20px; }}
    [data-testid="stWidgetLabel"] p {{ font-weight: 700; color: #334155; font-size: 1.1rem !important; }}
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important; border: 1px solid #1e3a8a !important; border-radius: 8px !important; height: 42px !important;
    }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; font-weight: 800; font-size: 1.2rem; }}
    .stTabs [aria-selected="true"] {{ background-color: #1e3a8a !important; color: white !important; border-radius: 8px 8px 0 0; }}
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)

# --- 3. 手勢導航 (解決手機滑動問題) ---
components.html("""
<script>
    const doc = window.parent.document;
    let startX = 0;
    doc.addEventListener('touchstart', e => { startX = e.changedTouches[0].screenX; }, {passive: true});
    doc.addEventListener('touchend', e => {
        let diff = startX - e.changedTouches[0].screenX;
        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
        let activeIdx = -1;
        tabs.forEach((t, i) => { if(t.getAttribute('aria-selected') === 'true') activeIdx = i; });
        if (Math.abs(diff) > 80) {
            if (diff > 0 && activeIdx < tabs.length - 1) tabs[activeIdx + 1].click();
            else if (diff < 0 && activeIdx > 0) tabs[activeIdx - 1].click();
        }
    }, {passive: true});
</script>
""", height=0)

# --- 4. 數據核心 ---
def get_ss():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

def fetch_data():
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        # 數值正規化：確保「預購餘量」邏輯正確
        for col in ['預購總量', '當日批價量', '預購餘量', '數量']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# --- 5. 主程式分頁 ---
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    rk = st.session_state.rk
    df_main = fetch_data()
    
    # 第一排
    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
    d_price = c2.selectbox("批價內容", ["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], key=f"pr_{rk}")
    d_hosp = c3.selectbox("使用醫院", ["慈濟", "門諾", "國軍", "部花"], key=f"hs_{rk}")

    # 第二排
    c4, c5, c6 = st.columns(3)
    d_pid = c4.text_input("病例號/ID", key=f"pi_{rk}")
    d_prod = c5.selectbox("產品項目", ["3E PRP", "Sportvis", "Holisoon"], key=f"pd_{rk}")
    d_dr = c6.text_input("醫師姓名", key=f"dr_{rk}")

    # 第三排：預購餘量計算區
    c7, c8, c9 = st.columns(3)
    d_pre_total, d_pre_today, d_qty, can_sub = 0, 0, 0, True
    
    if d_price == "使用前次預購":
        # 抓取該 病例號+產品 的最後一筆餘額
        res_df = df_main[(df_main['病例號/ID']==d_pid) & (df_main['產品項目']==d_prod)]
        cur_bal = int(res_df.iloc[-1]['預購餘量']) if not res_df.empty else 0
        if cur_bal > 0:
            c7.success(f"目前餘量：{cur_bal}")
            d_pre_today = c8.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}")
            d_qty = d_pre_today
        else:
            c7.error("⚠️ 餘額不足"); can_sub = False
    elif d_price == "批價 + 預購":
        d_pre_total = c7.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c8.number_input("當日扣除", min_value=1, value=1, key=f"py_{rk}")
        d_qty = d_pre_today
    elif d_price == "單次批價使用":
        d_qty = c7.number_input("數量", min_value=1, value=1, key=f"qt_{rk}")

    # 第四排：代表人員 (已更正名單)
    c10, c11, c12 = st.columns(3)
    # 這裡依照您的需求，欄位名稱為「跟刀人員」，名單鎖定為 Eric, 林國慈, 曾子榮
    d_rep = c10.selectbox("跟刀(操作)人員", ["Eric", "林國慈", "曾子榮"], key=f"rp_{rk}")
    d_memo = c11.text_area("備註", key=f"me_{rk}")
    
    if c12.button("🚀 提交存檔", use_container_width=True, disabled=not (can_sub and d_pid)):
        with st.spinner("存檔中..."):
            # 提交前再次抓取最新資料計算餘額
            latest_df = fetch_data()
            prev_res = latest_df[(latest_df['病例號/ID']==d_pid) & (latest_df['產品項目']==d_prod)]
            prev_bal = int(prev_res.iloc[-1]['預購餘量']) if not prev_res.empty else 0
            
            if d_price == "使用前次預購": final_bal = prev_bal - d_pre_today
            elif d_price in ["批價 + 預購", "純預購寄庫"]: final_bal = prev_bal + (d_pre_total - d_pre_today)
            else: final_bal = 0
            
            # 依照「回應試算表」欄位寫入：日期, 批價內容, 醫院, 科別, 醫師, 產品, 規格, 數量, 預購總量, 當日批價量, 預購餘量...
            row = [str(d_date), d_price, d_hosp, "", d_dr, d_prod, "", d_qty, d_pre_total, d_pre_today, final_bal, "", "", d_pid, "", "", "", d_rep, d_memo]
            ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
            st.toast("✅ 存檔成功！")
            time.sleep(1); st.session_state.rk += 1; st.rerun()

with tab2:
    # Page 2: 歷史紀錄 (手機端強化顯示)
    st.write("### 📊 最近 30 筆紀錄")
    st.dataframe(fetch_data().iloc[::-1].head(30), use_container_width=True, hide_index=True)

with tab3:
    # Page 3: 預購追蹤 (使用 st.table 確保手機不空白)
    st.write("### 🔍 剩餘預購名單")
    track_df = fetch_data()
    if not track_df.empty:
        # 篩選出最後餘額大於 0 的紀錄
        res = track_df.groupby(['病例號/ID', '產品項目']).tail(1)
        display_res = res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']]
        if not display_res.empty:
            st.table(display_res)
        else:
            st.info("目前無剩餘預購。")
