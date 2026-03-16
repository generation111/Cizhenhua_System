import streamlit as st

st.set_page_config(
    page_title="慈榛驊科技有限公司 - 業務管理總部",
    page_icon="🏢",
    layout="centered",  # 為了豎屏使用，改為集中佈局
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    /* 1. 解決標題被切割：增加上方邊距 */
    .block-container { 
        padding-top: 3rem !important; 
    }
    
    /* 2. 放大側邊欄文字：讓平板更容易點選 */
    [data-testid="stSidebarNav"] span {
        font-size: 20px !important;  /* 調整為您喜歡的大小 */
        font-weight: 500 !important;
    }
    
    /* 3. 主標題優化 */
    .main-title {
        text-align: center; 
        color: #1a1a1a; 
        font-size: 32px; 
        font-weight: bold;
        margin-bottom: 10px; 
        line-height: 1.4;
    }
    
    .sub-title {
        text-align: center; 
        color: #666; 
        font-size: 18px; 
        margin-bottom: 30px;
    }

    .system-card {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px;
        border: 1px solid #e0e0e0; 
        border-top: 5px solid #007bff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 主標題
    st.markdown("<div class='main-title'>慈榛驊科技有限公司<br>業務管理系統</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>專業、精準、高效的醫療行銷整合平台</div>", unsafe_allow_html=True)
    
    st.info("💡 請點擊左側選單切換功能。")

    # 豎屏時自動垂直排列
    st.markdown("""
        <div class='system-card'>
            <h3>🖋️ 跟刀紀錄管理</h3>
            <p>即時登錄手術耗材使用數據，數據自動同步雲端。</p>
        </div>
        <div class='system-card'>
            <h3>📊 報表管理系統</h3>
            <p>彙整雲端數據庫紀錄，提供視覺化分析圖表。</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption("版本代號：慈榛驊業務管理系統（全功能終極修復版） | © 2026 慈榛驊科技有限公司")

if __name__ == "__main__":
    main()