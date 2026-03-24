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

# --- 2. 樣式精修 (確保手機橫屏不跑版) ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1.5rem !important; background-color: #F0F9F0 !important; }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    .sys-title {{ text-align: center; font-size: 24px !important; font-weight: 900; color: #1e3a8a; margin-bottom: 10px !important; }}
    
    /* 輸入框高度與字體優化 */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important; border: 1px solid #1e3a8a !important; border-radius: 8px !important; height: 42px !important;
    }}
    .stTextInput input {{ height: 40px !important; font-size: 1.1rem !important; }}
    
    /* 分頁標籤手機端加大點擊區域 */
    .stTabs [data-baseweb="tab"] {{
        height: 50px !important; font-size: 1.1rem !important; font-weight: 800 !important;
    }}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動 (強化版：解決手機不給滑的問題) ---
components.html("""
<script>
    const container = window.parent.document.querySelector('.main');
    let startX = 0;
    
    window.parent.document.addEventListener('touchstart', e => {
        startX = e.touches[0].clientX;
    }, {passive: true});

    window.parent.document.addEventListener('touchend', e => {
        const endX = e.changedTouches[0].clientX;
        const diff = startX - endX;
        const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        let activeIdx = -1;
        tabs.forEach((t, i) => { if(t.getAttribute('aria-selected') === 'true') activeIdx = i; });

        if (Math.abs(diff) > 100) { // 滑動距離超過 100px
            if (diff > 0 && activeIdx < tabs.length - 1) tabs[activeIdx + 1].click(); // 左滑
            else if (diff < 0 && activeIdx > 0) tabs[activeIdx - 1].click(); // 右滑
            window.parent.scrollTo(0, 0);
        }
    }, {passive: true});
</script>
""", height=0)

# --- 4. 數據核心 (移除手機端不穩定的快取) ---
def get_ss():
    try:
        creds_info = st.secrets["gcp_service_account"].to_dict()
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    except: return None

ss = get_ss()

def fetch_all_data(no_cache=False):
    if not ss: return pd.DataFrame()
    try:
        ws = ss.worksheet("回應試算表")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            # 數值正規化
            for c in ['預購總量', '當日批價量', '預購餘量', '數量']:
                if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_current_balance(df, pid, prod):
    if df.empty or not pid or not prod: return 0
    # 這裡加入極端去空格化，對付手機輸入法
    pid_clean = str(pid).strip()
    prod_clean = str(prod).strip()
    mask = (df['病例號/ID'].astype(str).str.strip() == pid_clean) & \
           (df['產品項目'].astype(str).str.strip() == prod_clean)
    user_df = df[mask]
    if user_df.empty: return 0
    return int(user_df.iloc[-1]['預購餘量']) if '預購餘量' in user_df.columns else 0

# --- 5. 主介面 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料錄入", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    rk = st.session_state.rk
    db_df = fetch_all_data() # 第一頁可稍作緩存，但點擊提交後會重整

    c1, c2, c3 = st.columns(3)
    d_date = c1.date_input("日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
    d_dr = c2.text_input("醫師", key=f"dr_{rk}")
    d_content = c3.text_input("產品內容", key=f"cn_{rk}")
    
    c4, c5, c6 = st.columns(3)
    d_price = c4.selectbox("批價內容", ["單次批價使用", "批價 + 預購", "使用前次預購", "使用他人預購", "純預購寄庫"], key=f"pr_{rk}")
    
    # 初始化變數
    d_pre_total, d_pre_today, d_qty, can_submit = 0, 0, 0, True
    
    # 關鍵：為了讓手機即時抓到 ID，我們手動監測輸入
    c10, c11, c12 = st.columns(3)
    d_hosp = c10.selectbox("醫院", ["慈濟", "門諾", "國軍", "部花"], key=f"hs_{rk}")
    d_pid = c11.text_input("病例號/ID", key=f"pi_{rk}")
    d_dept = c12.selectbox("科別", ["骨科", "一般外科", "神經外科"], key=f"dp_{rk}")

    c7, c8, c9 = st.columns(3)
    d_prod = c7.selectbox("產品項目", ["3E PRP", "Sportvis", "Holisoon"], key=f"pd_{rk}")
    d_spec = c8.text_input("規格", key=f"sp_{rk}")
    d_pname = c9.text_input("病人名", key=f"pn_{rk}")

    # 邏輯判定區 (放在 ID 與 產品之後，確保手機端抓得到)
    if d_price == "使用前次預購":
        if d_pid and d_prod:
            cur_bal = get_current_balance(db_df, d_pid, d_prod)
            if cur_bal > 0:
                c6.success(f"餘量：{cur_bal}")
                d_pre_today = c5.number_input("扣除量", min_value=1, max_value=cur_bal, value=1, key=f"py_{rk}")
                d_qty = d_pre_today
            else:
                c5.error("餘額不足"); can_submit = False
        else:
            c5.warning("需輸入ID/產品"); can_submit = False
    elif d_price == "批價 + 預購":
        d_pre_total = c5.number_input("預購總量", min_value=1, value=5, key=f"pt_{rk}")
        d_pre_today = c6.number_input("當日扣除", min_value=1, value=1, key=f"py_{rk}"); d_qty = d_pre_today
    elif d_price == "單次批價使用":
        d_qty = c5.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_pre_today = d_qty

    c13, c14, c15 = st.columns(3)
    d_op = c13.text_input("部位", key=f"op_{rk}")
    d_loc = c14.selectbox("地點", ["血管攝影室", "開刀房"], key=f"lc_{rk}")
    d_blood = c15.selectbox("抽血", ["醫護人員", "跟刀人員"], key=f"bl_{rk}")
    
    c16, c17, c18 = st.columns(3)
    d_rep = c16.selectbox("代表", ["張家慈", "佰哥"], key=f"rp_{rk}")
    d_memo = c17.text_area("備註", key=f"me_{rk}")
    
    if c18.button("🚀 提交存檔", use_container_width=True, disabled=not can_submit):
        with st.spinner("存檔中..."):
            # 提交前最後計算
            latest_df = fetch_all_data(no_cache=True)
            bal = get_current_balance(latest_df, d_pid, d_prod)
            if d_price == "使用前次預購": bal -= d_pre_today
            elif d_price in ["批價 + 預購", "純預購寄庫"]: bal += (d_pre_total - d_pre_today)
            else: bal = 0
            
            row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_pre_total, d_pre_today, bal, d_content, d_pname, d_pid, d_op, d_loc, d_blood, d_rep, d_memo]
            ss.worksheet("回應試算表").append_row(row, value_input_option='USER_ENTERED')
            st.toast("✅ 已成功存檔！")
            time.sleep(1); st.session_state.rk += 1; st.rerun()

with tab2:
    st.write("### 📋 最近 50 筆紀錄")
    hist_df = fetch_all_data(no_cache=True)
    if not hist_df.empty:
        st.dataframe(hist_df.iloc[::-1].head(50), use_container_width=True, hide_index=True)

with tab3:
    st.write("### 🔍 剩餘預購追蹤")
    track_df = fetch_all_data(no_cache=True)
    if not track_df.empty:
        # 取最後餘額不為 0 的 ID
        res = track_df.groupby(['病例號/ID', '產品項目']).tail(1)
        res = res[res['預購餘量'] > 0][['病例號/ID', '產品項目', '預購餘量']]
        st.dataframe(res, use_container_width=True, hide_index=True)
