import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# --- 1. 系統基本設定 ---
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"

# --- 2. 縮放鎖定 (Viewport Lock) ---
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
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    [data-testid="stSidebarNav"] { background-color: transparent !important; }

    .block-container { 
        padding-top: 0.5rem !important; 
        max-width: 1300px !important; 
        margin: 0 auto !important; 
    }
    
    .sys-title { 
        text-align: center; 
        font-size: 24px !important; 
        font-weight: 850; 
        color: #1E3A8A; 
        margin-top: -55px !important; 
        margin-bottom: 10px !important;
        white-space: nowrap;
    }

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

    [data-testid="stHeader"] { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 4. 顯示系統標題 ---
st.markdown(f'<div class="sys-title">📊 {SYS_TITLE}</div>', unsafe_allow_html=True)

# --- 5. 更新後的資料連線函式 ---
@st.cache_data(ttl=60)
def load_all_data():
    try:
        # 取得金鑰並修復換行符號
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        # 使用您提供的新網址
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/edit"
        sh = gc.open_by_url(SHEET_URL)
        
        # 指定分頁名稱「表單回應 1」
        ws = sh.worksheet("表單回應 1")
        
        rows = ws.get_all_values()
        if not rows or len(rows) < 1:
            return pd.DataFrame()
            
        return pd.DataFrame(rows[1:], columns=rows[0])

    except Exception as e:
        st.error(f"❌ 讀取失敗：{str(e)}")
        service_email = st.secrets["gcp_service_account"]["client_email"]
        st.info(f"💡 請確保已將此表單『共用』給：\n\n`{service_email}`")
        return pd.DataFrame()

# --- 6. 報表顯示區 ---
st.subheader("📋 業務數據報表")

df = load_all_data()

if df is not None and not df.empty:
    # 簡單統計
    st.write(f"目前共有 {len(df)} 筆紀錄")
    
    # 搜尋功能
    search = st.text_input("🔍 搜尋醫師、醫院或代表姓名")
    if search:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search).any(), axis=1)]
    
    # 顯示表格
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("📊 雲端資料庫目前無資料或正在讀取中...")
