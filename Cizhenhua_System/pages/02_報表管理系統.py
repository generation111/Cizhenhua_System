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

# --- 2. UI 樣式優化 (框線強化 + 字體加大 + 高度 42px) ---
st.markdown("""
<style>
    .block-container { padding-top: 3.5rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
    .stApp { background-color: #F8FAFC; color: #000000; }
    label, p, span, div { color: #000000 !important; font-weight: 700 !important; }

    .sys-title { 
        text-align: center; font-size: 26px !important; font-weight: 900; 
        color: #1E3A8A !important; margin-bottom: 20px; 
    }
    
    .item-l { color: white !important; padding: 10px 15px; border-radius: 8px; font-weight: 700; margin: 15px 0 10px 0; font-size: 16px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    
    /* 所有錄入框高度 42px & 字體加大 & 藍色邊框 */
    div[data-baseweb="input"], div[data-baseweb="select"], .stDateInput div {
        background-color: white !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
        height: 42px !important;
    }

    input, .stSelectbox div[data-baseweb="select"] > div {
        font-size: 1.1rem !important;
        height: 40px !important;
        line-height: 28px !important;
    }

    /* 訪談內容錄入框高度縮減 */
    div[data-baseweb="textarea"] {
        min-height: 42px !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
    }
    textarea {
        height: 42px !important;
        font-size: 1.1rem !important;
        padding: 8px !important;
        line-height: 1.2 !important;
    }

    .stButton>button[kind="primary"] { 
        height: 45px !important; background-color: #2B6CB0 !important; color: white !important; font-size: 1.1rem !important;
    }
    button:has(div p:contains("🧹 清空")) {
        height: 45px !important; background-color: #E53E3E !important; color: white !important; border: none !important;
    }

    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動偵測腳本 ---
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

# --- 5. 行銷資料庫 (全數恢復鐵律版) ---
MARKETING_DB = {
    "Mocolax": {
        "full_name": "Mocolax 行銷指引 (Phenprobamate 400mg)",
        "focus": "🎯 **藥品特性**：中樞性肌肉鬆弛劑。\n- **臨床效益**：抑制 polysynaptic 反射，解除骨骼肌肉痙攣。\n- **病患好處**：迅速緩解腰背痛、肩酸。具安定效果，安全性優。",
        "action_table": [{"核心訴求": "解除痙攣", "目標": "迅速緩解", "行銷例句": "「醫師，Mocolax 作用於中樞，能迅速解除肌肉異常緊張。」"}],
        "dialogue": "「這顆藥能幫您舒緩肩頸背部的僵硬疼痛，讓肌肉放鬆。」",
        "manager": "🌟 **主管點評**：鎖定骨科與復健科。強調『速效、安定、安全』。"
    },
    "Kocel": {
        "full_name": "Kocel 行銷指引 (Psyllium Husk 1g)",
        "focus": "🎯 **藥品特性**：天然纖維素。\n- **臨床效益**：純天然植物外殼精製，非刺激性。\n- **病患好處**：溫和幫助排便，適合長期調節。",
        "action_table": [{"核心訴求": "天然調節", "目標": "軟便助排", "行銷例句": "「醫師，Kocel 是純天然纖維素，無刺激性。」"}],
        "dialogue": "「這是純天然植物纖維，能溫和幫助排便恢復正常。」",
        "manager": "🌟 **主管點評**：強調『純天然、無刺激、適合長期使用』。"
    },
    "Calmsit": {
        "full_name": "Calmsit 行銷指引 (痔瘡專用乳膏)",
        "focus": "🎯 **藥品特性**：抗炎+表面麻醉+收縮血管。\n- **臨床效益**：抗炎、止痛、止血三效合一，迅速消除痔核紅腫。",
        "action_table": [{"核心訴求": "三效配合", "目標": "消炎止血", "行銷例句": "「醫師，Calmsit 具備高倍抗炎效能，快速消痔。」"}],
        "dialogue": "「這支藥膏擦了之後，能很快緩解痔瘡的疼痛與出血。」",
        "manager": "🌟 **主管點評**：主打『三效合一、迅速消痔』。"
    },
    "Topcef": {
        "full_name": "Topcef 行銷指引 (Cephradine 500mg)",
        "focus": "🎯 **藥品特性**：第一代頭孢菌素。\n- **臨床效益**：廣譜抗菌，對 Penicillinase 菌株有效，吸收極快。",
        "action_table": [{"核心訴求": "廣譜殺菌", "目標": "快速控感", "行銷例句": "「醫師，Topcef 吸收極快，能提供穩定殺菌力。」"}],
        "dialogue": "「這款抗生素能針對您的發炎處快速作用，效果穩定。」",
        "manager": "🌟 **主管點評**：強調『吸收快、穩定殺菌、經典首選』。"
    },
    "速必一": {
        "full_name": "速必一 行銷指引 (FESPIXON)",
        "focus": "🎯 **藥品特性**：調節巨噬細胞極化 (M1/M2) 技術。\n- **臨床效益**：將發炎型轉化為修復型，重啟癒合機制。",
        "action_table": [{"核心訴求": "調節極化", "目標": "重啟癒合", "行銷例句": "「醫師，速必一從源頭轉化發炎環境。」"}],
        "dialogue": "「針對難癒合的傷口，速必一能從源頭重啟修復動力。」",
        "manager": "🌟 **主管點評**：鎖定 DFU 專業市場，強調機轉領先。"
    },
    "Biofermin-R": {
        "full_name": "Biofermin-R 行銷指引 (活性 R 菌)",
        "focus": "🎯 **藥品特性**：抗藥性活性乳酸菌製劑。\n- **臨床效益**：在抗生素環境下維持活性，重建腸道菌相。",
        "action_table": [{"核心訴求": "耐藥活性", "目標": "重建菌叢", "行銷例句": "「醫師，Biofermin-R 是唯一能與抗生素共存的菌株。」"}],
        "dialogue": "「服用抗生素時搭配 R 菌，能保護腸道健康，避免腹瀉。」",
        "manager": "🌟 **主管點評**：抗生素處方的必備搭檔。預防 AAD 第一品牌。"
    },
    "Nolidin": {
        "full_name": "Nolidin 行銷指引 (Butinoline HCl)",
        "focus": "🎯 **藥品特性**：解痙劑與多重制酸劑。\n- **臨床效益**：解除消化道平滑肌痙攣，中和胃酸。",
        "action_table": [{"核心訴求": "解痙制酸", "目標": "全效護胃", "行銷例句": "「醫師，Nolidin 雙效合一，能迅速解除絞痛。」"}],
        "dialogue": "「這顆藥能幫您的胃上一層保護層，解決胃絞痛不舒服。」",
        "manager": "🌟 **主管點評**：定位為『胃部黏膜的守門員』。"
    },
    "Sportvis": {
        "full_name": "Sportvis 行銷指引 (STABHA)",
        "focus": "🎯 **藥品特性**：專利生物修飾型透明質酸。\n- **臨床效益**：韌帶/肌腱周圍注射，縮短發炎期，功能重建。",
        "action_table": [{"核心訴求": "韌帶修復", "目標": "功能重建", "行銷例句": "「醫師，Sportvis 能讓扭傷的韌帶加速修復。」"}],
        "dialogue": "「這支注射劑能直接修復您受損的韌帶，比休息更快康復。」",
        "manager": "🌟 **主管點評**：鎖定自費市場，強調『精準修復、縮短病程』。"
    },
    "上療漾": {
        "full_name": "上療漾 行銷指引 (醫療級後生元)",
        "focus": "🎯 **藥品特性**：後生元專利配方。\n- **臨床效益**：強化黏膜屏障，調節菌相。",
        "action_table": [{"核心訴求": "黏膜護理", "目標": "完成療程", "行銷例句": "「醫師，上療漾能提升病患對化放療耐受度。」"}],
        "dialogue": "「治療期間搭配上療漾，幫助黏膜修復，維持體力。」",
        "manager": "🌟 **主管點評**：癌症照護輔助的首選。"
    },
    "喉立順": {
        "full_name": "喉立順 行銷指引 (Holisoon)",
        "focus": "🎯 **藥品特性**：水溶性甘菊藍消炎噴劑。\n- **臨床效益**：促進受損咽喉黏膜再生修復。",
        "action_table": [{"核心訴求": "消炎再生", "目標": "直接止痛", "行銷例句": "「醫師，喉立順直接修復發炎黏膜。」"}],
        "dialogue": "「喉嚨腫痛時噴一下，直接修復發炎處，安全有效。」",
        "manager": "🌟 **主管點評**：門診特色武器，推薦 ENT 使用。"
    }
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
    d_date = r1c1.date_input("日期", value=datetime.now(tw_tz).date(), key=f"dt_{rk}")
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
                st.table(pd.DataFrame(data["action_table"]))
                st.info(f"💬 **對話建議**：{data['dialogue']}")
                st.success(data["manager"])

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed")
    
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            ws = ss.worksheet("表單回應 1")
            row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
            ws.insert_row(row, 2, value_input_option='USER_ENTERED')
            st.toast("✅ 提交完成"); time.sleep(0.5)
            st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
    
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

with tab2:
    st.info("🔍 審閱管理模式 (左右滑動切換)")

with tab3:
    st.info("📜 歷史報表模式 (左右滑動切換)")
