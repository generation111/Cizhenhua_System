import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
current_date = datetime.now(tw_tz).date()
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

st.set_page_config(page_title=SYS_TITLE, layout="centered", initial_sidebar_state="collapsed")

# --- 2. 終極暴力 CSS：徹底移除所有篩選、排序、選單、工具欄 ---
st.markdown("""
<style>
    /* 基礎樣式 */
    .block-container { padding-top: 2rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
    .stApp { background-color: #F8FAFC; color: #000000; }
    .sys-title { text-align: center; font-size: 24px !important; font-weight: bold; color: #1E3A8A !important; margin-bottom: 10px; }
    .item-l { color: white !important; padding: 8px 15px; border-radius: 8px; font-weight: bold !important; margin: 10px 0 5px 0; font-size: 16px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    
    /* --- 【核心封印區】 --- */
    
    /* 1. 隱藏表格右側與表頭的所有互動圖示 (漏斗、三條線、選單) */
    [data-testid="stDataEditor"] button, 
    [data-testid="stDataEditor"] [role="button"],
    [data-testid="stDataEditor"] [data-testid="stDataEditorCanvas"] + div button {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. 徹底殺掉右上角的工具列 (Download, Search, Fullscreen) */
    [data-testid="stElementToolbar"] {
        display: none !important;
    }

    /* 3. 封鎖表頭點擊事件：讓滑鼠點不到任何排序或選單觸發點 */
    [data-testid="stDataEditor"] canvas + div > div > div:first-child {
        pointer-events: none !important;
    }
    
    /* 4. 針對彈出的選單容器 (Popover) 進行暴力隱藏 */
    div[data-baseweb="popover"], 
    div[role="menu"], 
    div[data-baseweb="menu"] {
        display: none !important;
        pointer-events: none !important;
    }

    /* 5. 修正表頭文字顏色與背景，確保視覺統一 */
    .st-emotion-cache-1pxm69b { background-color: #F1F5F9 !important; }

    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據與邏輯 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except: return None

ss = get_ss()

@st.cache_data(ttl=60)
def get_settings():
    d = {"times": ["請選擇", "上午", "下午", "晚上"], "reps": ["張家慈"], "hosps": [], "depts": []}
    if not ss: return d
    try:
        ws = ss.worksheet("Settings").get_all_values()
        df = pd.DataFrame(ws[1:], columns=ws[0])
        def cln(c): return [str(x).strip() for x in df[c].unique() if x and str(x).strip() != "請選擇"]
        return {"times": ["請選擇", "上午", "下午", "晚上"], "reps": cln("代表"), "hosps": cln("醫院"), "depts": cln("科別")}
    except: return d

settings = get_settings()

MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax 行銷指引 (Phenprobamate 400mg)", "focus": "🎯 **藥品特性**：中樞性肌肉鬆弛劑。\n- **臨床效益**：抑制 polysynaptic 反射，解除骨骼肌肉痙攣。", "dialogue": "「這顆藥能幫您舒緩肩頸背部的僵硬疼痛。」", "manager": "🌟 鎖定骨科與復健科。"},
    "Kocel": {"full_name": "Kocel 行銷指引 (Psyllium Husk 1g)", "focus": "🎯 **藥品特性**：天然纖維素。\n- **臨床效益**：溫和幫助排便。", "dialogue": "「這是純天然植物纖維。」", "manager": "🌟 強調純天然無刺激。"},
    "Calmsit": {"full_name": "Calmsit 行銷指引 (痔瘡專用乳膏)", "focus": "🎯 **藥品特性**：抗炎+表面麻醉+收縮血管。", "dialogue": "「緩解痔瘡的疼痛與出血。」", "manager": "🌟 主打三效合一。"},
    "Topcef": {"full_name": "Topcef 行銷指引 (Cephradine 500mg)", "focus": "🎯 **藥品特性**：第一代頭孢菌素。", "dialogue": "「抗生素能快速作用。」", "manager": "🌟 吸收快、穩定殺菌。"},
    "速必一": {"full_name": "速必一 行銷指引 (FESPIXON)", "focus": "🎯 **藥品特性**：調節巨噬細胞極化。", "dialogue": "「重啟傷口修復動力。」", "manager": "🌟 鎖定 DFU 專業市場。"},
    "Biofermin-R": {"full_name": "Biofermin-R 行銷指引 (活性 R 菌)", "focus": "🎯 **藥品特性**：抗藥性活性乳酸菌。", "dialogue": "「保護腸道健康，避免腹瀉。」", "manager": "🌟 抗生素處方必備。"},
    "Nolidin": {"full_name": "Nolidin 行銷指引 (Butinoline HCl)", "focus": "🎯 **藥品特性**：解痙劑與多重制酸劑。", "dialogue": "「解決胃絞痛不舒服。」", "manager": "🌟 胃部黏膜守門員。"},
    "Sportvis": {"full_name": "Sportvis 行銷指引 (STABHA)", "focus": "🎯 **藥品特性**：專利透明質酸。", "dialogue": "「直接修復受損韌帶。」", "manager": "🌟 鎖定自費市場。"},
    "上療漾": {"full_name": "上療漾 行銷指引 (醫療級後生元)", "focus": "🎯 **藥品特性**：後生元專利配方。", "dialogue": "「幫助黏膜修復，維持體力。」", "manager": "🌟 癌症照護首選。"},
    "喉立順": {"full_name": "喉立順 行銷指引 (Holisoon)", "focus": "🎯 **藥品特性**：甘菊藍消炎噴劑。", "dialogue": "「直接修復發炎處。」", "manager": "🌟 推薦 ENT 使用。"}
}

st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

# --- Tab 1: 錄入 ---
with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5); exp_p = st.container()
    st.markdown('<div class="item-l title-c">👤 2. 客戶基本資料</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    d_dt = c1.date_input("日期", value=current_date, key=f"dt_{rk}")
    d_tm = c2.selectbox("時段", settings["times"], key=f"t_{rk}")
    d_rp = c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    c4, c5, c6 = st.columns(3)
    d_hs = c4.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dp = c5.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = c6.text_input("醫師姓名", key=f"dr_{rk}")

    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp = p
            dr_txt = f"{d_dr}醫師" if d_dr else "醫師"
            st.session_state[f"n_{rk}"] = f"拜訪 {d_hs} {d_dp} {dr_txt}，介紹【{p}】臨床應用。"
            st.rerun()

    if st.session_state.cp:
        data = MARKETING_DB[st.session_state.cp]
        with exp_p:
            with st.expander(f"📚 {data['full_name']}", expanded=True):
                st.markdown(data["focus"]); st.info(f"💬 **建議**：{data['dialogue']}")

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed")
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            ws = ss.worksheet("表單回應 1")
            ws.insert_row([datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_dt), d_tm, d_rp, d_hs, d_dp, d_dr, st.session_state.cp, "待審閱", "", f_note], 2, value_input_option='USER_ENTERED')
            st.toast("✅ 提交完成"); time.sleep(0.5); st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

# --- Tab 2: 審閱管理 (終極封印過濾選單版) ---
with tab2:
    st.markdown("### 🔍 審閱管理 (批量核准模式)")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_df = pd.DataFrame(ws.get_all_records())
            if not all_df.empty and '審閱狀態' in all_df.columns:
                pnd = all_df[all_df['審閱狀態'] == '待審閱'].copy()
                if not pnd.empty:
                    sel_all = st.checkbox("✅ 全選所有待處理項目", key="global_select")
                    disp = pd.DataFrame({
                        "單選": [sel_all] * len(pnd),
                        "醫院": pnd['醫院'].tolist(),
                        "科別": pnd['科別'].tolist(),
                        "醫師": pnd['醫師姓名'].tolist(),
                        "產品": pnd['推廣產品'].tolist(),
                        "內容": pnd['訪談內容錄入'].tolist(),
                        "主管註記": pnd['主管註記'].tolist() if '主管註記' in pnd.columns else [""] * len(pnd)
                    })
                    
                    # 這裡是關鍵
                    edit_df = st.data_editor(
                        disp, 
                        column_config={
                            "單選": st.column_config.CheckboxColumn("單選", width="small"),
                            "主管註記": st.column_config.TextColumn("主管註記"),
                            "內容": st.column_config.TextColumn("內容", width="large", disabled=True),
                        }, 
                        hide_index=True, key="ed_t2", use_container_width=True, num_rows="fixed"
                    )

                    if st.button("🚀 批次提交審閱項目", type="primary", use_container_width=True):
                        s_rows = edit_df[edit_df["單選"] == True]
                        if not s_rows.empty:
                            with st.spinner("處理中..."):
                                for i in s_rows.index:
                                    ws.update_cell(pnd.index[i] + 2, 9, "已審閱")
                                    ws.update_cell(pnd.index[i] + 2, 10, edit_df.loc[i, "主管註記"])
                                st.success("✅ 已同步至雲端！"); time.sleep(1); st.cache_data.clear(); st.rerun()
                else: st.success("🎉 目前無待審閱資料。")
        except: st.error("連線異常")

with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            hist = pd.DataFrame(ws.get_all_records())
            if not hist.empty:
                st.dataframe(hist.sort_values(by="日期", ascending=False), use_container_width=True)
        except: st.error("讀取失敗")
