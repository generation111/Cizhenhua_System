import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# --- 1. 系統基本設定 ---
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

# --- 2. 縮放鎖定 (Viewport Lock) ---
# 強制手機 1:1 顯示，解決各分頁縮放連動問題
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

# --- 3. 樣式優化 (標題貼頂 + 移除白框 + 按鈕單行瘦身) ---
st.markdown("""
<style>
    /* 移除側邊欄多餘白框與背景優化 */
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    [data-testid="stSidebarNav"] { background-color: transparent !important; }

    /* 頁面內容寬度與貼頂設定 */
    .block-container { 
        padding-top: 0.5rem !important; 
        max-width: 1300px !important; 
        margin: 0 auto !important; 
    }
    
    /* 系統標題：極限貼頂 */
    .sys-title { 
        text-align: center; 
        font-size: 24px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -55px !important; 
        margin-bottom: 10px !important;
        white-space: nowrap;
    }

    /* 產品按鈕瘦身：高度縮小、文字絕對單行 */
    div.stButton > button {
        height: 35px !important;
        padding: 0px 4px !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background-color: white !important;
    }
    
    div.stButton > button p {
        white-space: nowrap !important;
        font-size: 13px !important;
        margin: 0 !important;
        overflow: hidden;
    }

    /* 隱藏頂部預設橫條 */
    [data-testid="stHeader"] { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 4. 顯示系統標題 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)

# --- 5. 官方推薦穩定連線法 (修復 Response 200 問題) ---
def load_all_data():
    try:
        # 使用 Streamlit 內建連線工具，它比純 gspread 更能處理 secrets 格式問題
        from streamlit_gsheets import GSheetsConnection
        
        # 建立連線 (它會自動去找 secrets 裡的 gcp_service_account)
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 直接讀取工作表
        # 參數說明：worksheet 是分頁名稱，ttl 是快取時間（秒）
        df = conn.read(
            worksheet="回應試算表",
            ttl="10m"
        )
        
        return df
    except Exception as e:
        # 備援方案：如果沒有安裝 st-gsheets，就用回傳統方式但加入強效格式化
        try:
            info = dict(st.secrets["gcp_service_account"])
            # 強制修復可能出錯的換行符號
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            gc = gspread.authorize(creds)
            
            # 改用 ID 開啟是最穩的 (請填入您的 ID)
            sh = gc.open_by_key("1B_pS9y6-v_CqMv6lO6U5oB3hS3O0_X4q8j-S9v6M123") 
            ws = sh.worksheet("回應試算表")
            rows = ws.get_all_values()
            return pd.DataFrame(rows[1:], columns=rows[0])
        except Exception as e2:
            st.error(f"❌ 雲端資料庫讀取失敗: {str(e2)}")
            return pd.DataFrame()

# --- 6. 報表顯示區 ---
st.subheader("📋 業務數據報表")

df = load_all_data()

if df is not None and not df.empty:
    # 這裡顯示資料表格
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    # 如果還在轉圈圈，顯示手動重整按鈕
    if st.button("🔄 手動重新整理資料"):
        st.cache_data.clear()
        st.rerun()

