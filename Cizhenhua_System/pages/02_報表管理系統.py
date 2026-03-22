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

# --- Tab 2: 審閱管理 (手動條列式模式) ---
with tab2:
    st.markdown("### 🔍 審閱管理 (條列式核准模式)")
    if ss:
        try:
            ws = ss.worksheet("表單回應 1")
            all_data = pd.DataFrame(ws.get_all_records())
            if not all_data.empty:
                pending = all_data[all_data['審閱狀態'] == '待審閱'].copy()
                if not pending.empty:
                    # 1. 表頭 (Header) - 手動拼裝
                    st.markdown("""
                    <div style="background-color: #F1F5F9; padding: 10px; border-radius: 5px; margin-bottom: 5px; border: 1px solid #E2E8F0;">
                        <div style="display: flex; flex-direction: row; font-weight: bold; color: #475569; font-size: 14px;">
                            <div style="flex: 0.5;">選取</div>
                            <div style="flex: 1.5;">醫院/科別/醫師</div>
                            <div style="flex: 1;">推廣產品</div>
                            <div style="flex: 2.5;">訪談內容</div>
                            <div style="flex: 1.5;">主管註記</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 全選功能
                    select_all = st.checkbox("✅ 全選所有待處理項目", key="global_select")
                    
                    # 儲存輸入內容的容器
                    updates = []

                    # 2. 表身 (Body) - 橫向條列
                    for idx, row in pending.iterrows():
                        col_sel, col_info, col_prod, col_cont, col_note = st.columns([0.5, 1.5, 1, 2.5, 1.5])
                        
                        # 單選勾選框
                        is_selected = col_sel.checkbox(" ", value=select_all, key=f"sel_{idx}", label_visibility="collapsed")
                        
                        # 醫師資訊
                        col_info.markdown(f"**{row['醫院']}**<br>{row['科別']} | {row['醫師姓名']}", unsafe_allow_html=True)
                        
                        # 產品
                        col_prod.write(row['推廣產品'])
                        
                        # 訪談內容 (使用 small 字體避免太擠)
                        col_cont.markdown(f"<div style='font-size: 13px; line-height: 1.4;'>{row['訪談內容錄入']}</div>", unsafe_allow_html=True)
                        
                        # 主管註記輸入框
                        mgr_note = col_note.text_input("註記", key=f"mgr_{idx}", label_visibility="collapsed", placeholder="輸入註記...")
                        
                        if is_selected:
                            updates.append({"idx": idx + 2, "note": mgr_note})
                        
                        st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #F1F5F9;'>", unsafe_allow_html=True)

                    # 3. 提交按鈕
                    if st.button("🚀 批次提交已選取的審閱項目", type="primary", use_container_width=True):
                        if updates:
                            with st.spinner("同步雲端中..."):
                                for item in updates:
                                    ws.update_cell(item["idx"], 9, "已審閱")
                                    ws.update_cell(item["idx"], 10, item["note"])
                                st.success(f"✅ 已成功核准 {len(updates)} 筆紀錄！")
                                time.sleep(1)
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.warning("請先勾選要核准的項目。")
                else:
                    st.success("🎉 目前無待審閱資料。")
        except Exception as e:
            st.error(f"連線異常: {e}")

with tab3:
    st.markdown("### 📜 歷史同步記錄")
    if ss:
        ws = ss.worksheet("表單回應 1")
        hist = pd.DataFrame(ws.get_all_records())
        st.dataframe(hist.sort_values(by="日期", ascending=False), use_container_width=True)
