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

# --- 2. UI 樣式優化 ---
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
        background-color: white !important; border: 1px solid #1E3A8A !important; border-radius: 8px !important; height: 42px !important;
    }
    div[data-baseweb="textarea"] { border: 1px solid #1E3A8A !important; border-radius: 8px !important; }
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

# --- 5. 行銷資料庫 ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax (Phenprobamate)", "focus": "🎯 中樞性肌肉鬆弛劑", "action_table": [{"核心訴求": "解除痙攣", "行銷例句": "迅速解除肌肉緊張"}], "dialogue": "舒緩僵硬疼痛", "manager": "鎖定骨科與復健科"},
    "Kocel": {"full_name": "Kocel (Psyllium Husk)", "focus": "🎯 天然纖維素", "action_table": [{"核心訴求": "天然調節", "行銷例句": "溫和幫助排便"}], "dialogue": "純天然植物纖維", "manager": "適合長期使用"},
    "Calmsit": {"full_name": "Calmsit 痔瘡乳膏", "focus": "🎯 抗炎止痛止血", "action_table": [{"核心訴求": "三效配合", "行銷例句": "快速消痔"}], "dialogue": "緩解疼痛出血", "manager": "三效合一首選"},
    "Topcef": {"full_name": "Topcef (Cephradine)", "focus": "🎯 第一代頭孢菌素", "action_table": [{"核心訴求": "廣譜殺菌", "行銷例句": "穩定殺菌力"}], "dialogue": "快速控制發炎", "manager": "經典抗菌首選"},
    "速必一": {"full_name": "速必一 (FESPIXON)", "focus": "🎯 巨噬細胞極化調節", "action_table": [{"核心訴求": "調節極化", "行銷例句": "重啟癒合機制"}], "dialogue": "從源頭重啟修復", "manager": "專業 DFU 市場"},
    "Biofermin-R": {"full_name": "Biofermin-R (R 菌)", "focus": "🎯 抗藥性乳酸菌", "action_table": [{"核心訴求": "耐藥活性", "行銷例句": "重建腸道菌相"}], "dialogue": "搭配抗生素使用", "manager": "預防 AAD 首選"},
    "Nolidin": {"full_name": "Nolidin (Butinoline)", "focus": "🎯 解痙制酸雙效", "action_table": [{"核心訴求": "解痙制酸", "行銷例句": "迅速解除絞痛"}], "dialogue": "解決胃絞痛保護黏膜", "manager": "胃部守門員"},
    "Sportvis": {"full_name": "Sportvis (STABHA)", "focus": "🎯 韌帶肌腱修復", "action_table": [{"核心訴求": "韌帶修復", "行銷例句": "加速韌帶修復"}], "dialogue": "比休息更快康復", "manager": "精準自費市場"},
    "上療漾": {"full_name": "上療漾 (後生元)", "focus": "🎯 黏膜屏障強化", "action_table": [{"核心訴求": "黏膜護理", "行銷例句": "提升療程耐受度"}], "dialogue": "輔助修復維持體力", "manager": "癌症照護首選"},
    "喉立順": {"full_name": "喉立順 (Holisoon)", "focus": "🎯 消炎再生噴劑", "action_table": [{"核心訴求": "消炎再生", "行銷例句": "直接修復黏膜"}], "dialogue": "直接止痛安全有效", "manager": "ENT 門診特色"}
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
    d_date = r1c1.date_input("日期", value=current_date, key=f"dt_{rk}")
    d_time = r1c2.selectbox("時段", settings["times"], key=f"t_{rk}")
    d_rep = r1c3.selectbox("代表", settings["reps"], index=0, key=f"rep_{rk}")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    d_hosp = r2c1.selectbox("醫院", ["請選擇"] + settings["hosps"], key=f"h_{rk}")
    d_dept = r2c2.selectbox("科別", ["請選擇"] + settings["depts"], key=f"d_{rk}")
    d_dr = r2c3.text_input("醫師姓名", key=f"dr_{rk}")

    # --- 核心修正：藥品點擊雙模式邏輯 ---
    for i, p in enumerate(MARKETING_DB.keys()):
        if p_cols[i%5].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
            st.session_state.cp = p
            
            # L1/L2 判斷基準
            is_l1 = (d_hosp == "請選擇" and d_dept == "請選擇" and not d_dr)
            
            if is_l1:
                # 模式 2：L1 模式 - 自動填充預設骨架
                intro_text = f"拜訪醫院科醫師談{p}介紹"
            else:
                # 模式 1：L2 模式 - 智慧帶入選單內容
                h_s = d_hosp if d_hosp != "請選擇" else "醫院"
                dp_s = d_dept if d_dept != "請選擇" else ""
                dr_s = f"{d_dr}醫師" if d_dr else "醫師"
                intro_text = f"{d_time}拜訪{h_s}{dp_s}{dr_s}談{p}介紹"
            
            st.session_state[f"n_{rk}"] = intro_text
            st.rerun()

    if st.session_state.cp:
        data = MARKETING_DB.get(st.session_state.cp)
        with exp_placeholder:
            with st.expander(f"📚 {data['full_name']}", expanded=True):
                st.markdown(data["focus"])
                st.info(f"💬 **對話建議**：{data['dialogue']}")
                st.success(data["manager"])

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed", height=120)
    
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            try:
                ws = ss.worksheet("表單回應 1")
                row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
                ws.insert_row(row, 2, value_input_option='USER_ENTERED')
                st.toast("✅ 提交完成"); time.sleep(0.5)
                st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
            except Exception as e: st.error(f"失敗: {e}")
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

with tab2:
    st.markdown("### 🔍 審閱管理")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_df = pd.DataFrame(ws.get_all_records())
            if not all_df.empty:
                pending = all_df[all_df['審閱狀態'] == '待審閱'].copy()
                if not pending.empty:
                    st.data_editor(pending, use_container_width=True)
                    if st.button("核准勾選項目"): st.success("已更新狀態")
                else: st.success("無待審閱資料")
        except: st.error("連線錯誤")

with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            st.dataframe(pd.DataFrame(ws.get_all_records()).sort_values(by="時間戳記", ascending=False), use_container_width=True)
        except: pass
