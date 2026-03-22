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

st.set_page_config(
    page_title=SYS_TITLE, 
    layout="centered", 
    initial_sidebar_state="collapsed" 
)

# --- 2. UI 樣式 ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
    .stApp { background-color: #F8FAFC; color: #000000; }
    label, p, span, div { color: #000000 !important; font-weight: normal !important; }
    .sys-title { text-align: center; font-size: 24px !important; font-weight: bold; color: #1E3A8A !important; margin-bottom: 10px; }
    .item-l { color: white !important; padding: 8px 15px; border-radius: 8px; font-weight: bold !important; margin: 10px 0 5px 0; font-size: 16px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-testid="stDateInput"] > div:first-child {
        background-color: white !important; border: 1px solid #1E3A8A !important; border-radius: 8px !important; height: 42px !important; box-sizing: border-box !important;
    }
    input, .stSelectbox div[data-baseweb="select"] > div { font-size: 1.1rem !important; height: 40px !important; line-height: 28px !important; }
    div[data-baseweb="textarea"] { min-height: 42px !important; border: 1px solid #1E3A8A !important; border-radius: 8px !important; }
    textarea { height: 42px !important; font-size: 1.1rem !important; padding: 8px !important; line-height: 1.2 !important; }
    .stButton>button[kind="primary"] { height: 45px !important; background-color: #2B6CB0 !important; color: white !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 手勢滑動偵測 ---
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
        tabs.forEach((t, i) => { if(t.getAttribute('aria-selected')===='true') active=i; });
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
        return {"times": ["上午", "下午", "晚上"], "reps": cln("代表"), "hosps": cln("醫院"), "depts": cln("科別")}
    except: return d

settings = get_settings()

# --- 行銷指引資料庫 ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax (Phenprobamate 400mg)", "focus": "🎯 中樞性肌肉鬆弛劑。解除骨骼肌肉痙攣。", "dialogue": "「這顆藥能幫您舒緩肩頸背部的僵硬疼痛。」"},
    "Kocel": {"full_name": "Kocel (Psyllium Husk 1g)", "focus": "🎯 天然纖維素。溫和幫助排便。", "dialogue": "「這是純天然植物纖維。」"},
    "Calmsit": {"full_name": "Calmsit (痔瘡專用乳膏)", "focus": "🎯 抗炎+止痛+止血三效合一。", "dialogue": "「擦了之後能很快緩解痔瘡疼痛。」"},
    "Topcef": {"full_name": "Topcef (Cephradine 500mg)", "focus": "🎯 第一代頭孢菌素。廣譜抗菌，吸收極快。", "dialogue": "「這款抗生素能針對發炎處快速作用。」"},
    "速必一": {"full_name": "速必一 (FESPIXON)", "focus": "🎯 調節巨噬細胞極化。重啟癒合機制。", "dialogue": "「針對難癒合傷口，重啟修復動力。」"},
    "Biofermin-R": {"full_name": "Biofermin-R (活性 R 菌)", "focus": "🎯 抗藥性活性乳酸菌。預防 AAD。", "dialogue": "「搭配抗生素保護腸道，避免腹瀉。」"},
    "Nolidin": {"full_name": "Nolidin (Butinoline HCl)", "focus": "🎯 解痙劑與多重制酸劑。全效護胃。", "dialogue": "「這顆藥能解決胃絞痛不舒服。」"},
    "Sportvis": {"full_name": "Sportvis (STABHA)", "focus": "🎯 專利透明質酸。修復韌帶/肌腱。", "dialogue": "「直接修復受損韌帶，加速康復。」"},
    "上療漾": {"full_name": "上療漾 (醫療級後生元)", "focus": "🎯 強化黏膜屏障。癌症照護輔助。", "dialogue": "「治療期間幫助黏膜修復。」"},
    "喉立順": {"full_name": "喉立順 (Holisoon)", "focus": "🎯 水溶性甘菊藍。修復咽喉黏膜。", "dialogue": "「噴一下直接修復發炎處。」"}
}

# --- 5. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

# --- Tab 1: 錄入功能 ---
with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5); exp_p = st.container()
    st.markdown('<div class="item-l title-c">👤 2. 客戶基本資料</div>', unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns(3)
    d_dt = r1c1.date_input("日期", value=current_date, key=f"dt_{rk}")
    d_tm = r1c2.selectbox("時段", settings["times"], key=f"t_{rk}")
    d_rp = r1c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    r2c1, r2c2, r2c3 = st.columns(3)
    d_hs = r2c1.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dp = r2c2.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = r2c3.text_input("醫師姓名", key=f"dr_{rk}")

    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp = p
            dr_s = f"{d_dr}醫師" if d_dr else "醫師"
            st.session_state[f"n_{rk}"] = f"拜訪 {d_hs} {d_dp} {dr_s}，介紹【{p}】。"
            st.rerun()

    if st.session_state.cp:
        data = MARKETING_DB[st.session_state.cp]
        with exp_p:
            with st.expander(f"📚 {data['full_name']}", expanded=True):
                st.markdown(data["focus"]); st.info(f"💬 {data['dialogue']}")

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

# --- Tab 2: 審閱管理 (純淨條列式，無 Data Editor 篩選坑) ---
with tab2:
    st.markdown("### 🔍 審閱管理 (條列式模式)")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_df = pd.DataFrame(ws.get_all_records())
            if not all_df.empty and '審閱狀態' in all_df.columns:
                pnd = all_df[all_df['審閱狀態'] == '待審閱'].copy()
                if not pnd.empty:
                    # 全選開關
                    sel_all = st.checkbox("✅ 全選所有待處理項目", key="global_select")
                    
                    # 自定義表頭
                    st.markdown("""
                    <div style="background-color: #F1F5F9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #E2E8F0; display: flex; font-weight: bold; color: #475569; font-size: 14px;">
                        <div style="flex: 0.5;">選取</div>
                        <div style="flex: 1.5;">醫院/科別/醫師</div>
                        <div style="flex: 1;">產品</div>
                        <div style="flex: 2.5;">訪談內容</div>
                        <div style="flex: 1.5;">主管註記</div>
                    </div>
                    """, unsafe_allow_html=True)

                    upds = []
                    for idx, row in pnd.iterrows():
                        c_sel, c_inf, c_prd, c_txt, c_mng = st.columns([0.5, 1.5, 1, 2.5, 1.5])
                        
                        is_sel = c_sel.checkbox(" ", value=sel_all, key=f"s_{idx}", label_visibility="collapsed")
                        c_inf.markdown(f"**{row['醫院']}**<br>{row['科別']} | {row['醫師姓名']}", unsafe_allow_html=True)
                        c_prd.write(row['推廣產品'])
                        c_txt.markdown(f"<div style='font-size:13px;'>{row['訪談內容錄入']}</div>", unsafe_allow_html=True)
                        m_note = c_mng.text_input("註記", key=f"m_{idx}", label_visibility="collapsed")
                        
                        if is_sel:
                            upds.append({"idx": idx + 2, "note": m_note})
                        st.markdown("<hr style='margin: 5px 0; border: 0.1px solid #F1F5F9;'>", unsafe_allow_html=True)

                    if st.button("🚀 批次提交審閱", type="primary", use_container_width=True):
                        if upds:
                            with st.spinner("同步中..."):
                                for item in upds:
                                    ws.update_cell(item["idx"], 9, "已審閱")
                                    ws.update_cell(item["idx"], 10, item["note"])
                                st.success(f"✅ 已完成 {len(upds)} 筆核准"); time.sleep(1); st.cache_data.clear(); st.rerun()
                        else: st.warning("請先勾選項目。")
                else: st.success("🎉 目前無待審閱資料。")
        except: st.error("數據連線異常")

# --- Tab 3: 歷史報表 ---
with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            hist = pd.DataFrame(ws.get_all_records())
            if not hist.empty:
                st.dataframe(hist.sort_values(by="日期", ascending=False), use_container_width=True)
        except: st.error("讀取失敗")
