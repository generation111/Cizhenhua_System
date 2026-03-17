import streamlit as st
import streamlit.components.v1 as components  # <---

# 強制寫入 Meta Tag 鎖定縮放 (Viewport Lock)
components.html(
    """
    <script>
        var meta = document.createElement('meta');
        meta.name = "viewport";
        meta.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0";
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    height=0,
)

# --- 修改樣式區塊，確保文字與按鈕不會因為縮放而跑位 ---
st.markdown("""
<style>
    /* 讓整個系統容器自適應，不論縮放比例 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }
    
    .block-container { 
        padding-top: 2rem !important; 
        max-width: 100% !important; 
    }

    /* 針對頂部主選單按鈕的優化 */
    div.stButton > button {
        white-space: nowrap; /* 確保按鈕文字不換行 */
        font-size: 14px !important; /* 固定字體大小，不隨系統縮放混亂 */
    }
</style>
""", unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務報表管理系統"

st.set_page_config(
    page_title=f"{SYS_TITLE}", 
    layout="centered", 
    initial_sidebar_state="collapsed" 
)

# --- 2. 側邊欄與 UI 樣式優化 ---
st.markdown("""
<style>
    .block-container { padding-top: 2.5rem !important; }
    [data-testid="stSidebarNav"] span { font-size: 22px !important; font-weight: bold !important; }
    [data-testid="column"] { display: flex; align-items: flex-end; }
    .stApp { background-color: #F8FAFC; }
    .sys-title { text-align: center; font-size: 26px !important; font-weight: 850; color: #1E3A8A; margin-bottom: 20px; }
    .item-l { color: white; padding: 10px 15px; border-radius: 8px; font-weight: 700; margin: 15px 0 10px 0; font-size: 14px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    .stButton>button { height: 45px !important; border-radius: 8px !important; }
    div[data-baseweb="textarea"] { min-height: 40px !important; }
    footer {visibility: hidden;}
    .info-bar { display: flex; justify-content: space-between; background: #EDF2F7; padding: 10px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #2B6CB0; }
    .info-item { font-size: 14px; color: #2D3748; }
</style>
""", unsafe_allow_html=True)

# --- 3. 全域手勢支援 ---
swipe_js = """
<script>
    const doc = window.parent.document;
    let startX = 0; let startY = 0;
    doc.addEventListener('touchstart', function(e) { startX = e.touches[0].clientX; startY = e.touches[0].clientY; }, {passive: false});
    doc.addEventListener('touchend', function(e) {
        const endX = e.changedTouches[0].clientX; const endY = e.changedTouches[0].clientY;
        const diffX = endX - startX; const diffY = endY - startY;
        const screenHeight = window.parent.innerHeight;
        const isTopOrBottom = (startY < screenHeight * 0.25) || (startY > screenHeight * 0.75);
        if (isTopOrBottom && Math.abs(diffX) > 50 && Math.abs(diffY) < 40) {
            const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
            let activeIdx = -1;
            tabs.forEach((tab, index) => { if (tab.getAttribute('aria-selected') === 'true') activeIdx = index; });
            if (diffX > 50 && activeIdx > 0) { tabs[activeIdx - 1].click(); } 
            else if (diffX < -50 && activeIdx < tabs.length - 1) { tabs[activeIdx + 1].click(); }
        }
    }, {passive: false});
</script>
"""
components.html(swipe_js, height=0)

# --- 4. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

ss = get_ss()

@st.cache_data(ttl=60)
def get_settings_data():
    default_vals = {"times": ["上午", "下午", "晚上"], "reps": ["張家慈"], "hosps": [], "depts": []}
    if not ss: return default_vals
    try:
        ws = ss.worksheet("Settings")
        data = ws.get_all_values()
        df_set = pd.DataFrame(data[1:], columns=data[0])
        def clean_list(series): return [str(x).strip() for x in series.unique() if x and str(x).strip() != "請選擇"]
        return {
            "times": clean_list(df_set["時段"]) if "時段" in df_set.columns else default_vals["times"],
            "reps": clean_list(df_set["代表"]) if "代表" in df_set.columns else default_vals["reps"],
            "hosps": clean_list(df_set["醫院"]) if "醫院" in df_set.columns else [],
            "depts": clean_list(df_set["科別"]) if "科別" in df_set.columns else []
        }
    except: return default_vals

settings = get_settings_data()

@st.cache_data(ttl=15)
def load_all_data():
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            data = ws.get_all_values()
            return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
        except: return pd.DataFrame()
    return pd.DataFrame()

all_df = load_all_data()

# ======================================================================================
# 【系統鐵律：完整行銷指引資料庫】
# ======================================================================================
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

# --- 5. 頁面佈局 ---
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
    d_time = r1c2.selectbox("時段", ["請選擇"] + settings["times"], key=f"t_{rk}")
    d_rep = r1c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    d_hosp = r2c1.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dept = r2c2.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = r2c3.text_input("醫師姓名", key=f"dr_{rk}", placeholder="請輸入姓名")

    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp = p
            t_s = f"{d_time} " if d_time != "請選擇" else ""
            h_s = d_hosp if d_hosp != "請選擇" else "醫院"
            dr_s = f"{d_dr}醫師" if d_dr != "" else "醫師"
            st.session_state[f"n_{rk}"] = f"{t_s}於{h_s}拜訪{dr_s}，進行【{p}】介紹與應用說明"
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
    f_note = st.text_area("內容", key=f"n_{rk}", label_visibility="collapsed", placeholder="內容自動生成處...")
    
    btn_c1, btn_c2 = st.columns([4, 1])
    if btn_c1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note:
            with st.spinner("同步中..."):
                try:
                    ws = ss.worksheet("表單回應 1")
                    row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
                    ws.insert_row(row, 2, value_input_option='USER_ENTERED')
                    st.cache_data.clear(); st.toast("✅ 提交成功"); time.sleep(0.5); st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
                except: st.error("提交失敗，請檢查網路")

    if btn_c2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

# --- Tab 2: 審閱管理 ---
with tab2:
    st.subheader("🔍 審閱管理")
    if not all_df.empty:
        pending = all_df[all_df['審閱狀態'] == '待審閱'].copy()
        if not pending.empty:
            select_all = st.checkbox("✅ 全選項目", key="global_select")
            display_df = pd.DataFrame({"選取": [select_all] * len(pending), "內容": pending['訪談內容錄入'].tolist(), "主管註記": pending['主管註記'].tolist()})
            edited_df = st.data_editor(display_df, column_config={"選取": st.column_config.CheckboxColumn(width=60), "內容": st.column_config.TextColumn(width=450, disabled=True)}, hide_index=True, key="editor_tab2")
            if st.button("🚀 批次提交核准", use_container_width=True):
                ws = ss.worksheet("表單回應 1")
                for i in edited_df[edited_df["選取"] == True].index:
                    row_idx = pending.index[i] + 2
                    ws.update_cell(row_idx, 9, "已審閱")
                    ws.update_cell(row_idx, 10, edited_df.loc[i, "主管註記"])
                st.cache_data.clear(); st.rerun()
        else: st.info("尚無待審閱資料")

# --- Tab 3: 歷史報表 ---
with tab3:
    curr_sys_date = datetime.now(tw_tz).strftime("%Y-%m-%d")
    st.markdown(f'<div class="info-bar"><div class="info-item">👤 業務代表：<b>張家慈</b></div><div class="info-item">📅 系統日期：<b>{curr_sys_date}</b></div></div>', unsafe_allow_html=True)
    if not all_df.empty:
        st.dataframe(all_df, use_container_width=True, hide_index=True)
