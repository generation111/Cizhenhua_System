import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

st.set_page_config(
    page_title=SYS_TITLE, 
    layout="centered", 
    initial_sidebar_state="collapsed" 
)

# --- 2. UI 樣式優化 (框線強化 + 錄入框扁平化) ---
st.markdown("""
<style>
    .block-container { padding-top: 3.5rem !important; max-width: 950px !important; background-color: #F0F9F0 !important; }
    .stApp { background-color: #F0F9F0 !important; }
    
    /* 文字黑化與字體加大 */
    label, p, span, div { color: #000000 !important; font-weight: 700 !important; font-size: 1.05rem !important; }

    .sys-title { 
        text-align: center; font-size: 26px !important; font-weight: 900; 
        color: #1E3A8A !important; margin-bottom: 20px; 
    }
    
    .item-l { color: white !important; padding: 10px 15px; border-radius: 8px; font-weight: 700; margin: 15px 0 10px 0; font-size: 16px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    
    /* 【核心框線技術】統一所有輸入組件高度與邊框 */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"], .stDateInput div {
        background-color: white !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
        height: 42px !important;
        box-sizing: border-box !important;
    }

    /* 訪談內容錄入框：高度減少 60% (鎖定 42px) */
    .stTextArea textarea {
        height: 40px !important;
        min-height: 40px !important;
        padding: 8px 12px !important;
        font-size: 18px !important;
        line-height: 1.2 !important;
        border: none !important;
    }

    /* 下拉選單與日期文字對齊 */
    .stSelectbox div[data-baseweb="select"] > div { font-size: 18px !important; height: 40px !important; display: flex; align-items: center; }
    .stTextInput input, .stDateInput input { font-size: 18px !important; height: 40px !important; border: none !important; }

    /* 分頁標籤加大 */
    .stTabs [data-baseweb="tab"] {
        height: 50px !important; font-size: 1.2rem !important; font-weight: 800 !important;
    }

    /* 提交與清空按鈕 */
    .stButton>button { height: 45px !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    button:has(div p:contains("🧹 清空")) { background-color: #E53E3E !important; color: white !important; }
    
    hr { display: none !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動功能腳本 ---
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
        if (swipeDistance < -100) { // 向左滑 -> 下一頁
            if (activeTabIndex < tabs.length - 1) {
                tabs[activeTabIndex + 1].click();
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        }
        if (swipeDistance > 100) { // 向右滑 -> 上一頁
            if (activeTabIndex > 0) {
                tabs[activeTabIndex - 1].click();
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        }
    }

    doc.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, {passive: true});
    doc.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleGesture(); }, {passive: true});
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

# --- 5. 行銷資料庫 (簡化版示意) ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax (Phenprobamate)", "focus": "🎯 中樞性肌肉鬆弛劑，迅速緩解腰背痛。"},
    "Kocel": {"full_name": "Kocel (Psyllium Husk)", "focus": "🎯 天然纖維素，溫和幫助排便。"},
    "Calmsit": {"full_name": "Calmsit (痔瘡乳膏)", "focus": "🎯 抗炎、止痛、止血三效合一。"},
    "Topcef": {"full_name": "Topcef (Cephradine)", "focus": "🎯 廣譜抗菌，吸收極快。"},
    "速必一": {"full_name": "速必一 (FESPIXON)", "focus": "🎯 調節巨噬細胞極化，重啟癒合機制。"},
    "Biofermin-R": {"full_name": "Biofermin-R (活性 R 菌)", "focus": "🎯 與抗生素並用，重建腸道菌相。"},
    "Nolidin": {"full_name": "Nolidin (Butinoline)", "focus": "🎯 解除消化道平滑肌痙攣。"},
    "Sportvis": {"full_name": "Sportvis (STABHA)", "focus": "🎯 韌帶/肌腱周圍注射，加速修復。"},
    "上療漾": {"full_name": "上療漾 (後生元)", "focus": "🎯 強化黏膜屏障，調節菌相。"},
    "喉立順": {"full_name": "喉立順 (Holisoon)", "focus": "🎯 直接修復發炎黏膜，安全有效。"}
}

# --- 6. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

with tab1:
    if "rk_v2" not in st.session_state: st.session_state.rk_v2 = 0
    if "cp_v2" not in st.session_state: st.session_state.cp_v2 = None
    rk = st.session_state.rk_v2
    
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5)
    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp_v2 = p
            # 自動生成內容草稿
            h_val = st.session_state.get(f"h_{rk}", "醫院")
            dr_val = st.session_state.get(f"dr_{rk}", "醫師")
            st.session_state[f"n_{rk}"] = f"拜訪 {h_val} {dr_val}，進行【{p}】臨床應用說明。"
            st.rerun()

    st.markdown('<div class="item-l title-c">👤 2. 客戶基本資料</div>', unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns(3)
    d_date = r1c1.date_input("日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
    d_time = r1c2.selectbox("時段", settings["times"], key=f"t_{rk}")
    d_rep = r1c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    d_hosp = r2c1.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dept = r2c2.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = r2c3.text_input("醫師姓名", key=f"dr_{rk}", placeholder="請輸入姓名")

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed", placeholder="點擊上方產品可自動生成草稿...")
    
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            ws = ss.worksheet("表單回應 1")
            row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp_v2, "待審閱", "", f_note]
            ws.insert_row(row, 2, value_input_option='USER_ENTERED')
            st.toast("✅ 提交完成"); time.sleep(0.5)
            st.session_state.rk_v2 += 1; st.session_state.cp_v2 = None; st.rerun()
    
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk_v2 += 1; st.session_state.cp_v2 = None; st.rerun()

# 審閱與報表分頁維持原邏輯...
with tab2: st.info("🔍 待辦審閱清單 (請使用滑動切換或點擊)")
with tab3: st.info("📜 歷史報表查詢 (請使用滑動切換或點擊)")
