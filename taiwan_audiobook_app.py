import streamlit as st
import easyocr
import asyncio
import edge_tts
import os
import tempfile
from PIL import Image, ImageOps  # 加入 ImageOps 來處理方向
import numpy as np

st.set_page_config(page_title="台灣腔紙本有聲書", page_icon="🎙️")

st.title("🎙️ 台灣腔紙本有聲書轉換器")
st.markdown("請確保照片光線充足，文字方向正確。")

# 強制使用 CPU 模式，避免雲端搜尋 GPU 導致逾時
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_tra', 'en'], gpu=False)

# 嘗試載入 OCR，如果還在下載模型會顯示提示
try:
    reader = load_ocr()
except Exception as e:
    st.warning("AI 大腦正在初始化中，請稍候 30 秒再重新整理網頁... ⏳")
    st.stop()

# 側邊欄與語速設定
st.sidebar.header("聲音設定")
voice_option = st.sidebar.selectbox("選擇語音", ["曉臻 (女聲)", "雲哲 (男聲)"])
voice_map = {"曉臻 (女聲)": "zh-TW-HsiaoChenNeural", "雲哲 (男聲)": "zh-TW-YunJheNeural"}
speed = st.sidebar.slider("語速 (%)", -50, 100, 20, 5)
speed_str = f"{'+' if speed >= 0 else ''}{speed}%"

uploaded_file = st.file_uploader("上傳書頁照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # 【關鍵修復】自動根據照片資訊 (EXIF) 轉正方向
    image = ImageOps.exif_transpose(image) 
    
    st.image(image, caption="已自動校正方向的照片", use_container_width=True)
    
    if st.button("開始轉成有聲書"):
        with st.spinner("正在辨識繁體中文..."):
            img_np = np.array(image)
            results = reader.readtext(img_np, detail=0)
            text = " ".join(results)
            
        if text.strip():
            st.success("辨識成功！")
            with st.expander("查看辨識出的文字"):
                st.write(text)
            
            with st.spinner("正在合成台灣腔語音..."):
                communicate = edge_tts.Communicate(text, voice_map[voice_option], rate=speed_str)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    asyncio.run(communicate.save(tmp.name))
                    st.audio(tmp.name, format="audio/mp3")
                    with open(tmp.name, "rb") as f:
                        st.download_button("下載 MP3", f, file_name="audiobook.mp3")
                os.remove(tmp.name)
        else:
            st.error("偵測不到文字，請確認照片是否清晰且沒有太嚴重的反光。")
