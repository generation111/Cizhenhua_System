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

# --- 2. UI 樣式優化 (Padding 調整至 3.2rem) ---
st.markdown("""
<style>
    .block-container { padding-top: 3.2rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
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
    
    div[data-baseweb="input"], 
    div[data-baseweb="select"], 
    div[data-testid="stDateInput"] > div:first-child {
        background-color: white !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
        height: 42px !important;
    }

    textarea {
        height: 42px !important; font-size: 1.1rem !important;
        padding: 8px !important; line-height: 1.2 !important;
    }

    .report-card {
        background: white; padding: 12px; border-radius: 8px;
        border-left: 5px solid #2B6CB0; margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: black !important;
    }

    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        # 指向佰哥提供的試算表
        return gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

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

# --- 4. 行銷資料庫 ---
MARKETING_DB = {
    "Mocolax": {"full_name": "Mocolax (Phenprobamate)", "focus": "🎯 中樞肌肉鬆弛劑"},
    "Kocel": {"full_name": "Kocel (Psyllium Husk)", "focus": "🎯 天然纖維素"},
    "Calmsit": {"full_name": "Calmsit (痔瘡乳膏)", "focus": "🎯 抗炎止痛止血"},
    "Topcef": {"full_name": "Topcef (Cephradine)", "focus": "🎯 第一代頭孢菌素"},
    "速必一": {"full_name": "速必一 (FESPIXON)", "focus": "🎯 傷口癒合調節"},
    "Biofermin-R": {"full_name": "Biofermin-R (活性 R 菌)", "focus": "🎯 抗藥性乳酸菌"},
    "Nolidin": {"full_name": "Nolidin (Butinoline HCl)", "focus": "🎯 解痙制酸"},
    "Sportvis": {"full_name": "Sportvis (STABHA)", "focus": "🎯 韌帶精準修復"},
    "上療漾": {"full_name": "上療漾 (後生元)", "focus": "🎯 黏膜修復照護"},
    "喉立順": {"full_name": "喉立順 (Holisoon)", "focus": "🎯 咽喉消炎噴劑"}
}

# --- 5. 頁面佈局 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

# --- Tab 1: 錄入邏輯 (雙模式 L1/L2) ---
with tab1:
    if "rk" not in st.session_state: st.session_state.rk = 0
    if "cp" not in st.session_state: st.session_state.cp = None
    rk = st.session_state.rk
    
    st.markdown('<div class="item-l title-p">🚀 1. 產品快速選取</div>', unsafe_allow_html=True)
    p_cols = st.columns(5)
    
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
            is_empty = (d_hosp == "請選擇" and d_dept == "請選擇" and not d_dr)
            if is_empty:
                final_text = f"拜訪醫院科醫師 介紹{p}臨床應用"
            else:
                h_s = d_hosp if d_hosp != "請選擇" else ""
                dp_s = d_dept if d_dept != "請選擇" else ""
                dr_s = f"{d_dr}醫師" if d_dr else "醫師"
                final_text = f"{d_time}拜訪{h_s}{dp_s}{dr_s} 介紹{p}臨床應用"
            st.session_state[f"n_{rk}"] = final_text
            st.rerun()

    st.markdown('<div class="item-l title-n">✍️ 3. 訪談內容錄入</div>', unsafe_allow_html=True)
    f_note = st.text_area("內容錄入", key=f"n_{rk}", label_visibility="collapsed")
    
    b1, b2 = st.columns([4, 1])
    if b1.button("🚀 提交同步記錄", type="primary", use_container_width=True):
        if not f_note: st.warning("內容不可為空")
        elif ss:
            try:
                ws = ss.worksheet("表單回應 1")
                row = [datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S"), str(d_date), d_time, d_rep, d_hosp, d_dept, d_dr, st.session_state.cp, "待審閱", "", f_note]
                ws.insert_row(row, 2, value_input_option='USER_ENTERED')
                st.toast("✅ 已提交"); time.sleep(0.5)
                st.session_state.rk += 1; st.session_state.cp = None; st.rerun()
            except Exception as e: st.error(f"提交失敗: {e}")

    if b2.button("🧹 清空", use_container_width=True):
        st.session_state.rk += 1; st.session_state.cp = None; st.rerun()

# --- Tab 2: 審閱管理 (修復邏輯) ---
with tab2:
    st.markdown("### 🔍 待審閱清單")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty and '審閱狀態' in df.columns:
                pending = df[df['審閱狀態'] == "待審閱"]
                if pending.empty:
                    st.success("目前暫無待審閱資料。")
                else:
                    for idx, row in pending.iterrows():
                        # 計算在試算表中的實際行號 (Header=1, list index starts 0, insert_row pushes down)
                        actual_row = idx + 2 
                        with st.container():
                            st.markdown(f"""
                            <div class="report-card">
                                <b>📍 {row.get('醫院','未知')} - {row.get('科別','')} ({row.get('醫師姓名','')})</b><br>
                                ⏱️ {row.get('日期','')} | 📦 {row.get('產品','')}<br>
                                📝 {row.get('訪談內容概要','')}
                            </div>
                            """, unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([1, 1, 2])
                            comment = c3.text_input("批註建議", key=f"cmt_{idx}")
                            if c1.button("✅ 核准", key=f"app_{idx}"):
                                ws.update_cell(actual_row, 9, "已核准")
                                ws.update_cell(actual_row, 10, comment)
                                st.rerun()
                            if c2.button("❌ 駁回", key=f"rej_{idx}"):
                                ws.update_cell(actual_row, 9, "已駁回")
                                ws.update_cell(actual_row, 10, comment)
                                st.rerun()
        except Exception as e: st.error(f"讀取審閱清單出錯: {e}")

# --- Tab 3: 歷史報表 ---
with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_data = pd.DataFrame(ws.get_all_records())
            if not all_data.empty:
                # 依時間戳記倒序排列
                st.dataframe(all_data.sort_values(by="時間戳記", ascending=False), use_container_width=True)
            else:
                st.info("目前無任何歷史記錄。")
        except Exception as e: st.error(f"報表讀取失敗: {e}")
