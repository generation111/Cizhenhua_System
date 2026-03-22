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

# --- 2. UI 樣式 ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; max-width: 950px !important; background-color: #F8FAFC !important; }
    .stApp { background-color: #F8FAFC; color: #000000; }
    .sys-title { text-align: center; font-size: 24px !important; font-weight: bold; color: #1E3A8A !important; margin-bottom: 10px; }
    .item-l { color: white !important; padding: 8px 15px; border-radius: 8px; font-weight: bold !important; margin: 10px 0 5px 0; font-size: 16px; }
    .title-p { background: linear-gradient(90deg, #64748B, #94A3B8); }
    .title-c { background: linear-gradient(90deg, #475569, #64748B); }
    .title-n { background: linear-gradient(90deg, #1E293B, #334155); }
    
    /* 自定義 HTML 表格樣式：確保絕對無篩選按鈕 */
    .custom-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
    .custom-table th { background-color: #F1F5F9; color: #475569; padding: 12px; text-align: left; border-bottom: 2px solid #E2E8F0; font-size: 14px; }
    .custom-table td { padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 15px; color: #1E293B; }
    .custom-table tr:hover { background-color: #F8FAFC; }
    .input-note { width: 100%; border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---
@st.cache_resource(ttl=60)
def get_ss():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit")
    except: return None

ss = get_ss()

# ======================================================================================
# 系統功能區
# ======================================================================================
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 業務錄入", "🔍 審閱管理", "📜 歷史報表"])

# (Tab 1 業務錄入代碼保持不變，略)

with tab2:
    st.markdown("### 🔍 審閱管理 (手動審閱模式)")
    if ss:
        ws = ss.worksheet("表單回應 1")
        all_data = pd.DataFrame(ws.get_all_records())
        if not all_data.empty:
            pending = all_data[all_data['審閱狀態'] == '待審閱'].copy()
            if not pending.empty:
                st.write(f"目前有 **{len(pending)}** 筆待審閱資料")
                
                # 改用更直觀的單筆審閱模式，徹底跳過 st.data_editor 的坑
                for idx, row in pending.iterrows():
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**📍 {row['醫院']} - {row['科別']} - {row['醫師姓名']}** ({row['推廣產品']})")
                            st.text_area("訪談內容", value=row['訪談內容錄入'], disabled=True, key=f"note_{idx}")
                        with col2:
                            mgr_note = st.text_input("主管註記", key=f"mgr_{idx}")
                            if st.button("✅ 核准", key=f"ok_{idx}"):
                                ws.update_cell(idx + 2, 9, "已審閱")
                                ws.update_cell(idx + 2, 10, mgr_note)
                                st.toast(f"已核准 {row['醫師姓名']} 的紀錄")
                                time.sleep(0.5)
                                st.rerun()
                    st.divider()
            else:
                st.success("🎉 目前無待審閱資料。")

with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        ws = ss.worksheet("表單回應 1")
        hist = pd.DataFrame(ws.get_all_records())
        st.dataframe(hist.sort_values(by="日期", ascending=False), use_container_width=True)
