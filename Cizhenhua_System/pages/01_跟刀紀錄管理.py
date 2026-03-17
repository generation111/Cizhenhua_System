import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import time

# --- 1. 核心設定 ---
tw_tz = timezone(timedelta(hours=8))
SYS_TITLE = "慈榛驊業務管理系統（全功能終極修復版）"
SPREADSHEET_ID = "1w2BDsPHHxgaz6PJhoPLXdh0UQJplA6rr42wLoLQIM9s"

st.set_page_config(page_title=f"{SYS_TITLE}", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 樣式優化 (標題貼頂 + 單列對齊) ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
    .sys-title { 
        text-align: center; font-size: 26px !important; font-weight: 850; 
        color: #1E3A8A; margin-top: -10px !important; margin-bottom: 15px !important;
    }
    hr { display: none !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextArea"] label { display: none !important; }
    div[data-testid="stTextArea"] textarea { height: 40px !important; min-height: 40px !important; padding: 8px !important; }
    div.stButton > button { height: 40px !important; width: 100% !important; font-weight: bold !important; border: 2px solid #1E3A8A !important; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 數據連線 ---

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import base64

@st.cache_resource(ttl=60)
def get_ss():
    try:
        # 1. 取得基本資訊 (Secrets 裡只留這幾個，private_key 拿掉也沒關係)
        creds_info = st.secrets["gcp_service_account"].to_dict()
        
        # 2. 【化骨綿掌】直接把金鑰 Base64 寫死在代碼裡
        # 請將您金鑰轉出來的那一長串「沒有換行、沒有符號」的 Base64 貼在這裡
        PURE_B64_KEY = "XG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrTGNjUjVFVk5jVCtGXG5aMjBMVkViYnRDVDBsVUIwdVdBUGZQSjl2V0drWjhYS29PWFdRMFI3RGtzbmQyVGdlRUEzVTZlODFxUm9KSi9JXG5ROThKWUx0UmkwM0loaUlVSC9XWVQzTEtMc1JVeHFOV0V3VGx3QmgxVThYZFBwWTlWOWdLYVJsZDZ3T3RqYnBKXG5LNkxFenFSSWhIaTgwbzAra0dKME9MdGFIWGt5bmhLaU1PUG4ybzR5WWVhNDlyYjR4cFZVQUJ0TkNNdmhWQzI2XG5Ca0d3ZGE4SHdMY1RKVEhDdU9HdDFDeFhkVms5T2JXZGxTYktQaTlBTEt3dTdKV0o4bDNpcmdkNmpxV2M1S210XG5mN3pvNFRIaXFwZWNXYW14R01nZXFJWVhKRk51K0NHQkJNTHFMY1ByQnlvVmtILzd6ZDk4NGJ1TjRIdUp4NXJqXG45cEJsaDF0L0FnTUJBQUVDZ2dFQVhSTzBpVm9xWFBPZlBpQlhheU1OSnZ3czFoT3lIeTZYQ0IyRDVPeHFQSGVaXG5nMGxxRTRxS21wdHRSdHlWWDVNYkFya0xzRTF3MjVPSkxBK2p1a2hBaFhGaldVL2tuK3JnWFhJTTRVMHdRN21RXG5PVkZIcFZaMTRmNWxLWm8zRjhERmVKcmxrbVN5UVIvTFc0Sml3R1hPVzd1U0NBQVlwdFV0aW1vMXI2NGJJaDBKXG5NVmZKL09EZERWQjVESzJ1a20yWnYreFlEa0NNNXJIbElNcU5EOTFyWExwY0UwT3pjZE9SS2svY01BdndwM0FJXG5CY2pWaVk0Q0pXb2VTLzB6YTZJVDhzRmgyQ2plRHZ4THJLdWJiRy83UUFTMW9LRDdhQUNBRHJzREZNcnM2NlU5XG4renBhRFovd0JFTUxaRTZQdzNKQU9Ucjh5MXlBUTlCbFR2cGoxQXpTT1FLQmdRRGtKTnhqTHNSU2hMVVltaDJwXG5OUk5uaFBBRUg2TDROZUZFVGl0dk1rSWp3VVpxb21vMGN1cXlHOEVUbzJ4cWI3VUpHTmxIR3BuNDIwTW1scHlWXG5rRWpIenFubkFVNENjZHNYeWNsTjhQWnlqd3R4TXNlTmJ6Qm1OdjFTMEk4dk1sSzV4RDdrb0hNMis5WlVXTlBwXG5iQ2ZVaVZ2MDF6Uzgwb05wUFcvREFQMzJBd0tCZ1FEVlpqdDhuNDVONCt0d2Y2dk1Qc0VPbHY1WEhtTlo5Z1VNXG4rd0I0bnNzSkFPSVFvYXhyQUo5Mm9RZ0Z2NWxJN3JzZVhYbWNTZmlzUkR3VEhsQi8zR0FHcDluYVpzdEhXREZWXG4zTXBrMlFpOFQwbkUzTUI5U1VKZS9XemFHQ091aUQ1ZXBKaE5CVW9JZWFaV21iVUhmeEpEaHQwUlE1Z2ZPU0g2XG5KMUNzdXRFNTFRS0JnQXBKYXpLQnFsSjZMMXd6bnNEQlp1V1ZCZWw1cjdSM1lYZmQrbkZpRjc5YStKellRK2VuXG5ndE9URXNxYTVNbUx6ZUxpSHZIb3ppWjlaSEs1K2NkNG9QOTVYd25PY2tFRDl6Z0VYakpJZWlSQ05PYmV2a2F2XG5TOFJnR0Y0Q2oySTJaNnArb2NOWFJMcW04a3dOVVVqR0dxbW5vK0RQVDA1d1E0S2NSWXpLWDZrWEFvR0JBTFNCXG5iRElIR0t6ajdJUFZTbkZTWjZTNnJkcnRGbWJEQmhTcndBTkhka0JnWWRobG1OMU53cFRxczBtQmZ0eEZLendOXG5IMC9HOWpSbzUxUFlvWWoxMUxmc2hRY0xTa2xIM1R0ZXJraE5tT2tJUEVMcjQxcFdmSEN5OXI4b0NnNllxZ0VPXG5RdEZyZHVyaVU0UVBNaVJzSlB1L2VRRWdadTJLT3laSTJTR3lTRVlkQW9HQWZibjNqcytNUVFLbExQR3Jrb1NsXG5zemFBUXdPcDJxa2xzemRUbkFtMVZpMzJGOGVYdUZQTXhHdTdJdDVLbzU5cG5OcUJ4cFJwV2JKQm9uOGZxbTJ6XG54eU11S2RJN0VXYjBNc0JHY1Jza0FOWnZMODRtNm1FWUR4a2ttNjVUaU1tK1ZhOExWczhvT0g4N2ZiMFRyMXRNXG5HeUJpYU4wSGdLY21Nc0JxN1VwSnltUT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIs"
        
        # 3. 解碼回原始金鑰文字
        decoded_key = base64.b64decode(PURE_B64_KEY).decode("utf-8")
        
        # 4. 確保換行符號是 Google 認得的格式
        creds_info["private_key"] = decoded_key.replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
        
    except Exception as e:
        st.error(f"❌ 化骨綿掌失敗 (這妖孽太強了): {str(e)}")
        return None
ss = get_ss()

@st.cache_data(ttl=60)
def get_options():
    """抓取選單，若連線失敗則提供預設值防止當機"""
    default_opt = {
        "price": ["載入失敗"], "hosp": ["載入失敗"], "dept": ["載入失敗"],
        "prod": ["載入失敗"], "loc": ["血管攝影室", "開刀房"], "blood": ["載入失敗"], "rep": ["載入失敗"]
    }
    if not ss: return default_opt
    try:
        ws = ss.worksheet("Settings")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
        
        return {
            "price": [x for x in df["批價內容"].dropna().unique() if x] if "批價內容" in df.columns else ["欄位遺失"],
            "hosp": [x for x in df["使用醫院"].dropna().unique() if x] if "使用醫院" in df.columns else ["欄位遺失"],
            "dept": [x for x in df["使用科別"].dropna().unique() if x] if "使用科別" in df.columns else ["欄位遺失"],
            "prod": [x for x in df["產品項目"].dropna().unique() if x] if "產品項目" in df.columns else ["欄位遺失"],
            "loc": [x for x in df["使用地點"].dropna().unique() if x] if "使用地點" in df.columns else ["血管攝影室", "開刀房"],
            "blood": [x for x in df["抽血人員"].dropna().unique() if x] if "抽血人員" in df.columns else ["欄位遺失"],
            "rep": [x for x in df["跟刀(操作)人員"].dropna().unique() if x] if "跟刀(操作)人員" in df.columns else ["欄位遺失"]
        }
    except Exception:
        return default_opt

OPT = get_options()

# --- 4. 介面佈局 ---
st.markdown(f'<div class="sys-title">📋 {SYS_TITLE}</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🖋️ 資料登錄", "📊 歷史紀錄", "🔍 預購追蹤"])

with tab1:
    if "rk_v11" not in st.session_state: st.session_state.rk_v11 = 0
    rk = st.session_state.rk_v11
    
    # 資料輸入區
    c1, c2, c3 = st.columns(3); d_date = c1.date_input("使用日期", value=datetime.now(tw_tz).date(), key=f"d_{rk}"); d_dr = c2.text_input("醫師姓名", key=f"dr_{rk}"); d_content = c3.text_input("產品內容(含預購)", key=f"cn_{rk}")
    c4, c5, c6 = st.columns(3); d_price = c4.selectbox("批價內容", OPT.get("price"), key=f"pr_{rk}"); d_prod = c5.selectbox("產品項目", OPT.get("prod"), key=f"pd_{rk}"); d_pname = c6.text_input("病人名", key=f"pn_{rk}")
    c7, c8, c9 = st.columns(3); d_hosp = c7.selectbox("使用醫院", OPT.get("hosp"), key=f"hs_{rk}"); d_spec = c8.text_input("規格", key=f"sp_{rk}"); d_pid = c9.text_input("病例號/ID", key=f"pi_{rk}")
    c10, c11, c12 = st.columns(3); d_dept = c10.selectbox("使用科別", OPT.get("dept"), key=f"dp_{rk}"); d_qty = c11.number_input("數量", min_value=1, value=1, key=f"qt_{rk}"); d_opname = c12.text_input("手術名稱/部位", key=f"op_{rk}")
    c13, c14, c15 = st.columns(3); d_loc = c13.selectbox("使用地點", OPT.get("loc"), key=f"lc_{rk}"); d_blood = c14.selectbox("抽血人員", OPT.get("blood"), key=f"bl_{rk}"); d_rep = c15.selectbox("跟刀(人員)", OPT.get("rep"), key=f"rp_{rk}")

    bc1, bc2, bc3 = st.columns([0.3, 3.2, 1])
    with bc1: st.markdown('<p style="font-weight:bold; margin-top:8px;">備註</p>', unsafe_allow_html=True)
    with bc2: d_memo = st.text_area("", key=f"me_{rk}", height=40, placeholder="請輸入備註...")
    with bc3:
        if st.button("🚀 提交數據", key="submit_btn"):
            if ss:
                try:
                    ws_res = ss.worksheet("回應試算表")
                    row = [str(d_date), d_price, d_hosp, d_dept, d_dr, d_prod, d_spec, d_qty, d_content, d_pname, d_pid, d_opname, d_loc, d_blood, d_rep, d_memo]
                    ws_res.append_row(row, value_input_option='USER_ENTERED')
                    st.toast("✅ 資料已成功存檔"); time.sleep(1)
                    st.session_state.rk_v11 += 1
                    st.rerun()
                except Exception as e: st.error(f"寫入失敗: {str(e)}")
            else: st.error("連線未建立，無法存檔。")
