import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
from PIL import Image, ImageOps
import numpy as np

# 設定頁面
st.set_page_config(page_title="台灣腔紙本有聲書", page_icon="🎙️")
st.title("🎙️ 台灣腔紙本有聲書轉換器")

# 側邊欄設定
st.sidebar.header("聲音設定")
voice_option = st.sidebar.selectbox("選擇語音", ["曉臻 (女聲)", "雲哲 (男聲)"])
voice_map = {"曉臻 (女聲)": "zh-TW-HsiaoChenNeural", "雲哲 (男聲)": "zh-TW-YunJheNeural"}
speed = st.sidebar.slider("語速 (%)", -50, 100, 20, 5)
speed_str = f"{'+' if speed >= 0 else ''}{speed}%"

# 上傳檔案
uploaded_file = st.file_uploader("上傳書頁照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image) # 修復你提到的照片橫向問題
    st.image(image, caption="已讀取的照片 (已自動轉正)", use_container_width=True)
    
    if st.button("開始轉成有聲書"):
        # 只有按下去才載入 OCR 引擎，避免啟動當機
        with st.spinner("正在啟動 AI 大腦並下載模型 (第一次需較長時間，請耐心等候)..."):
            import easyocr # 延遲載入
            reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            
            img_np = np.array(image)
            results = reader.readtext(img_np, detail=0)
            text = " ".join(results)
            
        if text.strip():
            st.success("辨識完畢！")
            st.text_area("辨識出的文字：", text, height=150)
            
            with st.spinner("正在轉為台灣腔調..."):
                communicate = edge_tts.Communicate(text, voice_map[voice_option], rate=speed_str)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    asyncio.run(communicate.save(tmp.name))
                    st.audio(tmp.name)
                os.remove(tmp.name)
        else:
            st.error("找不到文字，請換張清楚一點的照片試試看。")

st.info("💡 提示：如果看到 'Oh no'，請點擊右邊選單的 'Reboot App' 並給它一分鐘時間冷靜。")
