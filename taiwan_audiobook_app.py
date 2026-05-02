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
    
    # 【關鍵修復】讀取手機照片的轉向數據並自動轉正
    image = ImageOps.exif_transpose(image)
    
    # 修正日誌中的警告：將 use_container_width=True 換成 width="stretch"
    st.image(image, caption="已讀取的照片 (已自動轉正)", width="stretch")
    
    if st.button("開始轉成有聲書"):
        with st.spinner("正在啟動 AI 大腦並辨識文字 (第一次下載模型需較長時間，請耐心等候)..."):
            import easyocr 
            # 強制使用 CPU 模式以確保穩定性
            reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            
            img_np = np.array(image)
            results = reader.readtext(img_np, detail=0)
            text = " ".join(results)
            
        if text.strip():
            st.success("辨識成功！")
            st.text_area("辨識出的文字：", text, height=150)
            
            with st.spinner("正在合成台灣腔語音..."):
                communicate = edge_tts.Communicate(text, voice_map[voice_option], rate=speed_str)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    asyncio.run(communicate.save(tmp.name))
                    st.audio(tmp.name)
                os.remove(tmp.name)
        else:
            st.error("拍謝，偵測不到文字，請確認照片文字是否清晰。")

st.info("💡 如果第一次按按鈕等很久是正常的，因為伺服器正在抓取辨識模型。")
