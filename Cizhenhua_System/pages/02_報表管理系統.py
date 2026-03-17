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
        padding-top: 2.5rem !important; 
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
        # 1. 取得金鑰與授權
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        # 2. 試算表網址 (已根據您的輸入校對)
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s/edit"
        
        # 使用網址開啟
        sh = gc.open_by_url(SHEET_URL)
        
        # 3. 指定分頁：根據您的網址 gid=1982907342，嘗試精確開啟
        # 我們先嘗試用名稱「回應試算表」，若失敗則嘗試該 gid 對應的分頁
        try:
            ws = sh.worksheet("回應試算表")
        except:
            # 如果名稱不對，改用暴力搜尋法找符合該 gid 的分頁
            ws = None
            for sheet in sh.worksheets():
                if str(sheet.id) == "1982907342":
                    ws = sheet
                    break
            if ws is None:
                ws = sh.get_worksheet(0) # 最終保險：開第一個
        
        rows = ws.get_all_values()
        if not rows:
            return pd.DataFrame()
            
        return pd.DataFrame(rows[1:], columns=rows[0])

    except Exception as e:
        # 這裡是解決 404 的終極提示
        st.error(f"❌ 讀取失敗：{str(e)}")
        # 顯示需要共用的 Email，方便佰哥直接複製
        service_email = st.secrets["gcp_service_account"]["client_email"]
        st.info(f"💡 請檢查：是否已將此試算表『共用』給以下 Email：\n\n`{service_email}`")
        return pd.DataFrame()

    except Exception as e:
        # 顯示更精確的錯誤訊息
        st.error(f"❌ 讀取失敗：{str(e)}")
        st.warning("請檢查：1. 網址是否正確 2. 試算表是否有共用給 Service Account 的 Email")
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

