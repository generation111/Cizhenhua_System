import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# --- 1. 系統基本設定 ---
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

# --- 2. 縮放鎖定 (Viewport Lock) ---
# 確保在手機上切換分頁時，比例保持 1:1，不會因為縮放而連動
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

# --- 3. 樣式優化 (標題貼頂 + 移除白框 + 瘦身按鈕) ---
st.markdown("""
<style>
    /* 移除側邊欄多餘白框 */
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    [data-testid="stSidebarNav"] { background-color: transparent !important; }

    /* 頁面內容寬度與貼頂設定 */
    .block-container { 
        padding-top: 1.0rem !important; 
        max-width: 1300px !important; 
        margin: 0 auto !important; 
    }
    
    /* 系統標題優化：向上衝頂 */
    .sys-title { 
        text-align: center; 
        font-size: 24px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -45px !important; 
        margin-bottom: 10px !important;
        white-space: nowrap;
    }

    /* 產品按鈕瘦身：高度縮小、文字單行 */
    div.stButton > button {
        height: 35px !important;
        padding: 0px 5px !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background-color: white !important;
    }
    
    div.stButton > button p {
        white-space: nowrap !important;
        font-size: 13px !important;
        margin: 0 !important;
    }

    /* 隱藏預設頁首橫條與頁尾 */
    [data-testid="stHeader"] { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 4. 顯示系統標題 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)

# --- 5. Google Sheets 連線與資料讀取 ---
# 這裡建議使用您的 Secrets 管理金鑰
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # 從 st.secrets 讀取憑證
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 開啟試算表 (請確保試算表名稱正確)
        sh = client.open("慈榛驊業務管理系統") # 請更換為您的試算表實際名稱
        ws = sh.worksheet("回應試算表")
        
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return pd.DataFrame()

# --- 6. 報表主要內容區 ---
st.subheader("📋 業務報表概覽")

all_df = load_all_data()

if not all_df.empty:
    # 這裡可以加入您的報表過濾或分析邏輯
    st.dataframe(all_df, use_container_width=True)
else:
    st.info("目前暫無資料或連線中...")

# 這裡可以繼續加入您的圖表分析（例如 st.bar_chart）
