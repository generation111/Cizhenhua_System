import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
now_dt = datetime.now(tw_tz)
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

st.set_page_config(
    page_title=SYS_TITLE, 
    layout="centered", 
    initial_sidebar_state="collapsed" 
)

# --- 2. UI 樣式優化 (強化邊框 + 壓縮間距) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
    .stApp { background-color: #F8FAFC; color: #000000; }
    
    label, p, span, div { color: #000000 !important; font-weight: normal !important; }

    .sys-title { 
        text-align: center; font-size: 24px !important; font-weight: bold; 
        color: #1E3A8A !important; margin-bottom: 10px; 
    }
    
    .item-l { 
        color: white !important; padding: 8px 15px; border-radius: 8px; 
        font-weight: bold !important; margin: 10px 0 5px 0; font-size: 16px; 
    }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    
    /* 輸入框：統一 42px 高度與藍色邊框 */
    div[data-baseweb="input"], 
    div[data-baseweb="select"], 
    div[data-testid="stDateInput"] > div:first-child {
        background-color: white !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
        height: 42px !important;
        box-sizing: border-box !important;
    }

    /* 確保日期框線存在且不重複 */
    div[data-testid="stDateInput"] { margin-bottom: 2px !important; }

    input, .stSelectbox div[data-baseweb="select"] > div {
        font-size: 1.1rem !important;
        height: 40px !important;
        line-height: 28px !important;
    }

    /* 訪談錄入框 */
    div[data-baseweb="textarea"] {
        min-height: 42px !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
    }
    textarea {
        height: 42px !important; font-size: 1.1rem !important;
        padding: 8px !important; line-height: 1.2 !important;
    }

    /* 審閱卡片 */
    .report-card {
        background: white; padding: 12px; border-radius: 8px;
        border-left: 5px solid #2B6CB0; margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .stButton>button[kind="primary"] { 
        height: 45px !important; background-color: #2B6CB0 !important; color: white !important;
    }
    
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動 ---
components.html("""
<script>
    const doc = window.parent.document;
    let startX = 0;
    doc.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, {passive: true});
    doc.addEventListener('touchend', e => {
        const endX = e.changedTouches[0].clientX;
        const diff = startX - endX;
        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
        let active = -1;
        tabs.forEach((t, i) => { if(t.getAttribute('aria-selected')==='true') active=i; });
        if (Math.abs(diff) > 100) {
            if (diff > 0 && active < tabs.length - 1) tabs[active+1].click();
            if (diff < 0 && active > 0) tabs[active-1].click();
            window.parent.scrollTo({top: 0, behavior: 'smooth'});
        }
    }, {passive: true});
</script>
""", height=0)

# --- 4. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except: return None

ss = get_ss()

@st.cache_data(ttl=60)
def get_settings():
    d = {"times": ["上午", "下午", "晚上"], "reps": ["張家慈"], "hosps": [], "depts": []}
    if not ss: return d
    try:
        ws = ss.worksheet("Settings").get_all_values()
        df = pd.DataFrame(ws[1:], columns=ws[0])
        def cln(c): return [str(x).strip() for x in df[c].unique() if x and str(x).strip() != "請選擇"]
        return {"times": cln("時段"), "reps": cln("代表"), "hosps": cln("醫院"), "depts": cln("科別")}
    except: return d

settings = get_settings()

# --- 5. 行銷資料庫 (鐵律版 - 簡略版顯示) ---
# (此處保留先前提供給您的完整字典數據內容即可)
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax 行銷指引 (Phenprobamate 400mg)", "focus": "🎯 **藥品特性**：中樞性肌肉鬆弛劑...", "action_table": [], "dialogue": "...", "manager": "..."},
    # ... 其他產品資料保持不變
}

# --- 6. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5)
    exp_placeholder = st.container()

    st.markdown('<div class="item-l title-c">👤 2. 客戶基本資料</div>', unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns(3)
    # 日期設為系統當前時間
    d_date = r1c1.date_input("日期", value=now_dt.date(), key=f"dt_{rk}")
    d_time = r1c2.selectbox("時段", settings["times"], key=f"t_{rk}")
    d_rep = r1c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    d_hosp = r2c1.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dept = r2c2.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = r2c3.text_input("醫師姓名", key=f"dr_{rk}")

    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp = p
            h_s = d_hosp if d_hosp != "請選擇" else "醫院"
            dr_s = f"{d_dr}醫師" if d_dr else "醫師"
            st.session_state[f"n_{rk}"] = f"拜訪 {h_s} {dr_s}，進行【{p}】臨床應用說明。"
            st.rerun()

    if st.session_state.cp:
        data = MARKETING_DB.get(st.session_state.cp)
        with exp_placeholder:
            with st.expander(f"📚 {data['full_name']}", expanded=True):
                st.markdown(data["focus"])
                st.info(f"💬 **建議**：{data['dialogue']}")

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed")
    
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            ws = ss.worksheet("表單回應 1")
            row = [now_dt.strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
            ws.insert_row(row, 2, value_input_option='USER_ENTERED')
            st.toast("✅ 提交完成")
            st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

with tab2:
    st.markdown("### 🔍 待審閱管理")
    if ss:
        ws = ss.worksheet("表單回應 1")
        df = pd.DataFrame(ws.get_all_records())
        pending = df[df['審閱狀態'] == "待審閱"]
        if pending.empty:
            st.info("目前沒有待處理的審閱項。")
        else:
            for i, row in pending.iterrows():
                st.markdown(f'<div class="report-card"><b>{row["醫院"]} {row["醫師姓名"]}</b><br>產品：{row["產品"]}<br>內容：{row["訪談內容概要"]}</div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1,1,2])
                comment = c3.text_input("批註", key=f"c_{i}")
                if c1.button("✅ 核准", key=f"ok_{i}"):
                    ws.update_cell(i+2, 9, "已核准"); ws.update_cell(i+2, 10, comment); st.rerun()
                if c2.button("❌ 駁回", key=f"no_{i}"):
                    ws.update_cell(i+2, 9, "已駁回"); ws.update_cell(i+2, 10, comment); st.rerun()

with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        ws = ss.worksheet("表單回應 1")
        all_df = pd.DataFrame(ws.get_all_records())
        st.dataframe(all_df.head(20), use_container_width=True)
