import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
from PIL import Image, ImageOps
import numpy as np

st.set_page_config(page_title="台灣腔紙本有聲書", page_icon="🎙️")
st.title("🎙️ 台灣腔紙本有聲書轉換器")

# 1. 預載入 OCR 引擎 (加上快取，避免重複載入)
@st.cache_resource
def get_reader():
    import easyocr
    return easyocr.Reader(['ch_tra', 'en'], gpu=False)

# 側邊欄設定
st.sidebar.header("聲音設定")
voice_option = st.sidebar.selectbox("選擇語音", ["曉臻 (女聲)", "雲哲 (男聲)"])
voice_map = {"曉臻 (女聲)": "zh-TW-HsiaoChenNeural", "雲哲 (男聲)": "zh-TW-YunJheNeural"}
speed = st.sidebar.slider("語速 (%)", -50, 100, 20, 5)
speed_str = f"{'+' if speed >= 0 else ''}{speed}%"

uploaded_file = st.file_uploader("上傳書頁照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 讀取並修正照片方向
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)
    
    # --- 【關鍵修復：照片瘦身術】 ---
    # 如果照片太大，強制縮小寬度到 1000 像素，避免記憶體爆炸
    max_width = 1000
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(float(image.height) * float(ratio))
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    # --------------------------------
    
    st.image(image, caption="已讀取的照片 (已自動轉正與優化大小)", width="stretch")
    
    if st.button("開始轉成有聲書"):
        try:
            with st.spinner("正在辨識文字 (第一次下載模型較久，請勿重複點擊)..."):
                reader = get_reader()
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
                st.warning("照片中似乎沒有偵測到文字喔！")
        except Exception as e:
            st.error(f"拍謝，發生了一點小錯誤。可能是伺服器還在下載模型，請稍候再試。")
