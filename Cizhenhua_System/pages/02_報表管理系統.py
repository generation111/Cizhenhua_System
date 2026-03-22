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
        background-color: white !important; border: 1px solid #1E3A8A !important; border-radius: 8px !important; height: 42px !important; box-sizing: border-box !important;
    }
    input, .stSelectbox div[data-baseweb="select"] > div { font-size: 1.1rem !important; height: 40px !important; line-height: 28px !important; }
    div[data-baseweb="textarea"] { min-height: 42px !important; border: 1px solid #1E3A8A !important; border-radius: 8px !important; }
    textarea { height: 42px !important; font-size: 1.1rem !important; padding: 8px !important; line-height: 1.2 !important; }
    .stButton>button[kind="primary"] { height: 45px !important; background-color: #2B6CB0 !important; color: white !important; }
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
    d = {"times": ["請選擇", "上午", "下午", "晚上"], "reps": ["張家慈"], "hosps": [], "depts": []}
    if not ss: return d
    try:
        ws = ss.worksheet("Settings").get_all_values()
        df = pd.DataFrame(ws[1:], columns=ws[0])
        def cln(c): return [str(x).strip() for x in df[c].unique() if x and str(x).strip() != "請選擇"]
        return {"times": ["請選擇", "上午", "下午", "晚上"], "reps": cln("代表"), "hosps": cln("醫院"), "depts": cln("科別")}
    except: return d

settings = get_settings()

# --- 5. 行銷資料庫 (佰哥鐵律，原封不動) ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax 行銷指引", "focus": "🎯 中樞性肌肉鬆弛劑...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Kocel": {"full_name": "Kocel 行銷指引", "focus": "🎯 天然纖維素...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Calmsit": {"full_name": "Calmsit 行銷指引", "focus": "🎯 痔瘡專用乳膏...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Topcef": {"full_name": "Topcef 行銷指引", "focus": "🎯 第一代頭孢菌素...", "action_table": [], "dialogue": "...", "manager": "..."},
    "速必一": {"full_name": "速必一 行銷指引", "focus": "🎯 調節巨噬細胞...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Biofermin-R": {"full_name": "Biofermin-R 行銷指引", "focus": "🎯 活性 R 菌...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Nolidin": {"full_name": "Nolidin 行銷指引", "focus": "🎯 解痙劑與多重制酸劑...", "action_table": [], "dialogue": "...", "manager": "..."},
    "Sportvis": {"full_name": "Sportvis 行銷指引", "focus": "🎯 專利透明質酸...", "action_table": [], "dialogue": "...", "manager": "..."},
    "上療漾": {"full_name": "上療漾 行銷指引", "focus": "🎯 醫療級後生元...", "action_table": [], "dialogue": "...", "manager": "..."},
    "喉立順": {"full_name": "喉立順 行銷指引", "focus": "🎯 水溶性甘菊藍...", "action_table": [], "dialogue": "...", "manager": "..."}
}

# --- 6. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

# --- Tab 1: 錄入功能 ---
with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5); exp_placeholder = st.container()
    st.markdown('<div class="item-l title-c">👤 2. 客戶基本資料</div>', unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns(3)
    d_date = r1c1.date_input("日期", value=current_date, key=f"dt_{rk}")
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
            dept_s = d_dept if d_dept != "請選擇" else "科"
            dr_s = f"{d_dr}醫師" if d_dr else "醫師"
            st.session_state[f"n_{rk}"] = f"拜訪 {h_s} {dept_s} {dr_s}，介紹【{p}】臨床應用說明。"
            st.rerun()

    if st.session_state.cp:
        data = MARKETING_DB.get(st.session_state.cp)
        with exp_placeholder:
            with st.expander(f"📚 {data['full_name']}", expanded=True):
                st.markdown(data["focus"]); st.info(f"💬 **對話建議**：{data['dialogue']}")

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed")
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if f_note and ss:
            ws = ss.worksheet("表單回應 1")
            row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
            ws.insert_row(row, 2, value_input_option='USER_ENTERED')
            st.toast("✅ 提交完成"); time.sleep(0.5); st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

# --- Tab 2: 審閱管理 (恢復全選 + 標題更名為「單選」) ---
with tab2:
    st.markdown("### 🔍 審閱管理 (批量操作模式)")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            data = ws.get_all_records()
            all_df = pd.DataFrame(data)
            
            if not all_df.empty and '審閱狀態' in all_df.columns:
                pending = all_df[all_df['審閱狀態'] == '待審閱'].copy()
                
                if not pending.empty:
                    # 恢復全選勾選框邏輯
                    select_all = st.checkbox("✅ 全選所有待處理項目", key="global_select")
                    
                    display_df = pd.DataFrame({
                        "選取": [select_all] * len(pending),
                        "審閱狀態": pending['審閱狀態'].tolist(),
                        "醫院": pending['醫院'].tolist(),
                        "科別": pending['科別'].tolist(),
                        "醫師姓名": pending['醫師姓名'].tolist(),
                        "推廣產品": pending['推廣產品'].tolist(),
                        "訪談內容錄入": pending['訪談內容錄入'].tolist(),
                        "主管註記": pending['主管註記'].tolist() if '主管註記' in pending.columns else [""] * len(pending)
                    })
                    
                    # 將標題「核准」改為「單選」
                    edited_df = st.data_editor(
                        display_df, 
                        column_config={
                            "選取": st.column_config.CheckboxColumn("單選", width="small"),
                            "審閱狀態": st.column_config.TextColumn("狀態", disabled=True),
                            "醫院": st.column_config.TextColumn("醫院", disabled=True),
                            "科別": st.column_config.TextColumn("科別", disabled=True),
                            "醫師姓名": st.column_config.TextColumn("醫師姓名", disabled=True),
                            "推廣產品": st.column_config.TextColumn("推廣產品", disabled=True),
                            "訪談內容錄入": st.column_config.TextColumn("訪談內容錄入", width="large", disabled=True),
                            "主管註記": st.column_config.TextColumn("主管註記")
                        }, 
                        hide_index=True, 
                        key="editor_tab2", 
                        use_container_width=True
                    )
                    
                    if st.button("🚀 批次提交審閱項目", type="primary", use_container_width=True):
                        selected_rows = edited_df[edited_df["選取"] == True]
                        if not selected_rows.empty:
                            with st.spinner(f"正在處理 {len(selected_rows)} 筆資料..."):
                                for i in selected_rows.index:
                                    row_idx = pending.index[i] + 2
                                    ws.update_cell(row_idx, 9, "已審閱")
                                    ws.update_cell(row_idx, 10, edited_df.loc[i, "主管註記"])
                                st.success(f"✅ 成功完成 {len(selected_rows)} 筆審閱！")
                                time.sleep(1); st.cache_data.clear(); st.rerun()
                        else:
                            st.warning("請勾選項目。")
                else:
                    st.success("🎉 目前無待審閱資料。")
        except Exception as e:
            st.error(f"錯誤: {e}")

# --- Tab 3: 歷史報表 ---
with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_data = pd.DataFrame(ws.get_all_records())
            if not all_data.empty:
                if "時間戳記" in all_data.columns:
                    all_data = all_data.drop(columns=["時間戳記"])
                st.dataframe(all_data.sort_values(by="日期", ascending=False), use_container_width=True)
            else:
                st.info("目前無歷史記錄。")
        except: st.error("報表讀取失敗")
