# --- 2. 樣式精修 (精準定位，不隱藏功能區) ---
st.markdown(f"""
<style>
    /* 1. 只針對頂部裝飾條透明化，不影響標籤功能 */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0) !important;
        height: 0px !important;
    }}
    
    /* 2. 修正容器 Padding，確保標題顯示在適當高度 */
    .block-container {{ 
        padding-top: 3.5rem !important; /* 縮減 padding，讓標題往上提 */
        max-width: 850px !important;
        background-color: #F0F9F0 !important; 
    }}
    .stApp {{ background-color: #F0F9F0 !important; }}
    
    /* 3. 標題樣式調整 */
    .sys-title {{ 
        text-align: center; 
        font-size: 32px !important; 
        font-weight: 900; 
        color: #1e3a8a; 
        margin-top: -10px !important; /* 向上微調 */
        margin-bottom: 20px !important; 
    }}
    
    /* 4. 統一輸入框高度與備註框對齊 */
    [data-testid="stWidgetLabel"] p {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; }}
    
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: white !important; 
        border: 2px solid #1e3a8a !important; 
        border-radius: 8px !important; 
        height: 45px !important;
    }}

    /* 備註框高度鎖定 */
    .stTextArea textarea {{
        height: 45px !important;
        min-height: 45px !important;
        padding: 8px 12px !important;
        line-height: 1.2 !important;
        resize: none !important;
    }}

    /* Tab 樣式保持可見與美觀 */
    .stTabs [data-baseweb="tab"] {{ 
        height: 52px !important; 
        font-weight: 800 !important; 
        font-size: 1.2rem !important; 
    }}
    .stTabs [aria-selected="true"] {{ 
        background-color: #1e3a8a !important; 
        color: white !important; 
    }}
    
    footer {{visibility: hidden;}}
</style>
<div class="sys-title">📋 {SYS_TITLE}</div>
""", unsafe_allow_html=True)
