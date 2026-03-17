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

# --- 5. 修正後的 Google Sheets 連線函式 ---
@st.cache_data(ttl=60)
def load_all_data():
    try:
        # 1. 從 Secrets 獲取憑證字典
        info = st.secrets["gcp_service_account"]
        
        # 2. 定義完整的權限範圍
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # 3. 建立憑證 (這是關鍵修復點：確保憑證物件完全建立)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        
        # 4. 使用 gspread.authorize 並明確指定憑證
        gc = gspread.authorize(creds)
        
        # 5. 開啟試算表 (佰哥，請再次確認您的試算表名稱是否為「慈榛驊業務管理系統」)
        # 如果還是不行，請換成 .open_by_key("您的試算表ID")
        sh = gc.open("慈榛驊業務管理系統")
        ws = sh.worksheet("回應試算表")
        
        # 6. 讀取並轉為 DataFrame
        rows = ws.get_all_values()
        if not rows:
            return pd.DataFrame()
        
        return pd.DataFrame(rows[1:], columns=rows[0])

    except Exception as e:
        # 如果失敗，顯示精確的錯誤類型
        st.error(f"❌ 連線異常: {type(e).__name__} - {str(e)}")
        return pd.DataFrame()

# --- 6. 報表顯示區 ---
st.subheader("📋 業務數據報表")

df = load_all_data()

if not df.empty:
    # 這裡顯示資料表格
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("📊 正在讀取雲端資料庫，請稍候...")

