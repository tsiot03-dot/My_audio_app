
import streamlit as st
import easyocr
import asyncio
import edge_tts
import os
import tempfile
from PIL import Image
import numpy as np

# 設定頁面資訊
st.set_page_config(page_title="台灣腔紙本有聲書轉換器", page_icon="🎙️")

st.title("🎙️ 台灣腔紙本有聲書轉換器")
st.markdown("上傳書頁照片，即刻轉換為親切的台灣人聲朗讀！")

# 初始化 OCR 引擎 (快取以提升效能)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_tra', 'en'])

reader = load_ocr()

# 側邊欄設定
st.sidebar.header("聲音設定")
voice_option = st.sidebar.selectbox(
    "選擇語音腔調",
    ["曉臻 (女聲 - 推薦)", "雲哲 (男聲)"],
    index=0
)

# 對應 edge-tts 的 voice ID
voice_map = {
    "曉臻 (女聲 - 推薦)": "zh-TW-HsiaoChenNeural",
    "雲哲 (男聲)": "zh-TW-YunJheNeural"
}

speed = st.sidebar.slider("朗讀速度 (%)", min_value=-50, max_value=100, value=20, step=5)
speed_str = f"{'+' if speed >= 0 else ''}{speed}%"

# 上傳檔案
uploaded_file = st.file_uploader("請選擇書頁照片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 顯示圖片
    image = Image.open(uploaded_file)
    st.image(image, caption="上傳的書頁", use_container_width=True)
    
    if st.button("開始辨識並轉換"):
        with st.spinner("正在閱讀文字中... (第一次執行較慢)"):
            # 轉換 PIL 圖片為 numpy array 給 easyocr
            img_np = np.array(image)
            results = reader.readtext(img_np, detail=0)
            text = " ".join(results)
            
        if text.strip():
            st.subheader("辨識出的文字：")
            st.write(text)
            
            with st.spinner("正在合成台灣腔語音..."):
                # 設定語音參數
                communicate = edge_tts.Communicate(text, voice_map[voice_option], rate=speed_str)
                
                # 建立暫存檔儲存 MP3
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    asyncio.run(communicate.save(tmp_file.name))
                    audio_path = tmp_file.name
                
                # 播放語音
                st.audio(audio_path, format="audio/mp3")
                
                # 提供下載
                with open(audio_path, "rb") as f:
                    st.download_button("下載語音檔 (MP3)", f, file_name="audiobook.mp3")
                
                # 清理暫存檔
                os.remove(audio_path)
        else:
            st.error("拍謝，偵測不到任何文字，請確保光線充足且字體清晰。")

st.info("💡 Vibe Coding 小撇步：如果想要語氣更自然，可以調整朗讀速度至 +15% 到 +25% 之間。")
