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

# --- 2. 側邊欄與 UI 樣式優化 (標題貼頂 + 瘦身按鈕) ---
st.markdown("""
<style>
    /* 移除側邊欄白框與標題貼頂 */
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    [data-testid="stSidebarNav"] { background-color: transparent !important; }
    .block-container { padding-top: 1.0rem !important; max-width: 1300px !important; margin: 0 auto !important; }
    
    /* 系統標題：極限貼頂 */
    .sys-title { 
        text-align: center; font-size: 24px !important; font-weight: 850; 
        color: #1E3A8A; margin-top: -45px !important; margin-bottom: 15px !important;
        white-space: nowrap;
    }

    /* 區塊標題 */
    .item-l { color: white; padding: 8px 12px; border-radius: 6px; font-weight: 700; margin: 10px 0 8px 0; font-size: 13px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }

    /* 產品按鈕：瘦身單行化 */
    div.stButton > button {
        height: 35px !important;
        padding: 0px 2px !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background-color: white !important;
    }
    div.stButton > button p {
        white-space: nowrap !important;
        font-size: 13px !important;
        margin: 0 !important;
    }

    footer {visibility: hidden;}
    [data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 全域手勢支援 (Viewport Lock) ---
components.html("""
<script>
    var meta = document.createElement('meta');
    meta.name = "viewport";
    meta.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0";
    document.getElementsByTagName('head')[0].appendChild(meta);
</script>
""", height=0)

# --- 4. 數據連線 (修復 Response 200 問題) ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        # 使用佰哥指定的最新網址
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

ss = get_ss()

# --- 數據讀取邏輯 ---
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

# --- 5. 行銷指引資料庫 (已修正 Nolidin 名稱) ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax (Phenprobamate 400mg)", "focus": "🎯 中樞性肌肉鬆弛劑", "action_table": [{"核心訴求": "解除痙攣"}], "dialogue": "解除肌肉僵硬", "manager": "🌟 鎖定骨科復健科"},
    "Kocel": {"full_name": "Kocel (Psyllium Husk 1g)", "focus": "🎯 天然纖維素", "action_table": [{"核心訴求": "天然調節"}], "dialogue": "溫和幫助排便", "manager": "🌟 強調純天然"},
    "Calmsit": {"full_name": "Calmsit 痔瘡乳膏", "focus": "🎯 抗炎+表面麻醉", "action_table": [{"核心訴求": "消炎止痛"}], "dialogue": "快速緩解紅腫", "manager": "🌟 三效合一"},
    "Topcef": {"full_name": "Topcef (Cephradine 500mg)", "focus": "🎯 第一代頭孢菌素", "action_table": [{"核心訴求": "廣譜殺菌"}], "dialogue": "快速控感效果穩定", "manager": "🌟 吸收快首選"},
    "速必一": {"full_name": "速必一 (FESPIXON)", "focus": "🎯 調節巨噬細胞極化", "action_table": [{"核心訴求": "重啟癒合"}], "dialogue": "源頭轉化傷口環境", "manager": "🌟 DFU 專業領先"},
    "Biofermin-R": {"full_name": "Biofermin-R (活性 R 菌)", "focus": "🎯 抗藥性乳酸菌", "action_table": [{"核心訴求": "重建菌叢"}], "dialogue": "抗生素最佳搭檔", "manager": "🌟 預防 AAD"},
    "Nolidin": {"full_name": "Nolidin (Butinoline HCl)", "focus": "🎯 解痙劑與制酸劑", "action_table": [{"核心訴求": "解除絞痛"}], "dialogue": "胃黏膜保護層", "manager": "🌟 胃部守門員"},
    "Sportvis": {"full_name": "Sportvis (STABHA)", "focus": "🎯 專利透明質酸", "action_table": [{"核心訴求": "韌帶修復"}], "dialogue": "加速受損修復", "manager": "🌟 鎖定自費市場"},
    "上療漾": {"full_name": "上療漾 (後生元)", "focus": "🎯 強化黏膜屏障", "action_table": [{"核心訴求": "癌症照護"}], "dialogue": "提升療程耐受度", "manager": "🌟 化放療首選"},
    "喉立順": {"full_name": "喉立順 (Holisoon)", "focus": "🎯 甘菊藍消炎噴劑", "action_table": [{"核心訴求": "黏膜再生"}], "dialogue": "直接修復發炎處", "manager": "🌟 ENT 特色武器"}
}

# --- 6. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_keys = list(MARKETING_DB.keys())
    for i in range(0, len(p_keys), 5):
        cols = st.columns(5)
        for j, p in enumerate(p_keys[i:i+5]):
            if cols[j].button(p, key=f"btn_{p}_{rk}", use_container_width=True):
                st.session_state.cp = p
                t_s = f"{st.session_state.get(f't_{rk}', '時段')} "
                h_s = st.session_state.get(f'h_{rk}', '醫院')
                dr_s = st.session_state.get(f'dr_{rk}', '醫師')
                # 鐵律：不加「於」，代表名稱張家慈後不加贅字
                st.session_state[f"n_{rk}"] = f"{t_s}{h_s}拜訪{dr_s}，進行【{p}】介紹與應用說明"
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

    if st.session_state.cp:
        data = MARKETING_DB.get(st.session_state.cp)
        with st.expander(f"📚 {data['full_name']}", expanded=True):
            st.markdown(data["focus"])
            st.info(f"💬 **對話建議**：{data['dialogue']}")

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容", key=f"n_{rk}", label_visibility="collapsed", placeholder="點擊上方產品自動生成...")
    
    if st.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and d_hosp != "請選擇":
            with st.spinner("同步中..."):
                try:
                    ws = ss.worksheet("表單回應 1")
                    row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
                    ws.insert_row(row, 2, value_input_option='USER_ENTERED')
                    st.cache_data.clear(); st.toast("✅ 提交成功"); time.sleep(0.5); st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
                except: st.error("提交失敗，請檢查網路")
        else: st.warning("請填寫醫院並確保有錄入內容")

# --- Tab 2: 審閱管理 ---
with tab2:
    if not all_df.empty:
        pending = all_df[all_df['審閱狀態'] == '待審閱'].copy()
        if not pending.empty:
            edited_df = st.data_editor(pending[['訪談內容錄入', '主管註記']], use_container_width=True)
            if st.button("🚀 批次提交核准"):
                st.toast("功能更新中..."); st.cache_data.clear(); st.rerun()
        else: st.info("尚無待審閱資料")

# --- Tab 3: 歷史報表 ---
with tab3:
    if not all_df.empty:
        st.dataframe(all_df, use_container_width=True, hide_index=True)
