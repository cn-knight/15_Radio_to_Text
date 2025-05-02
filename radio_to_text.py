"""
FM音乐源播放器与实时语音转文字应用
该脚本实现了一个基于Streamlit的FM电台播放器，集成了Deepgram API实现实时语音转文字功能。
主要功能：播放多个在线电台、录制麦克风音频、实时转录音频流内容，并在UI中展示转录结果。
"""

import streamlit as st
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import httpx
import threading
import pyaudio
import time

# 加载环境变量并初始化Deepgram客户端
load_dotenv()
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
deepgram = DeepgramClient(api_key=deepgram_api_key)

# 定义语音服务
speech_services = {
    "Deepgram": {"key": deepgram_api_key, "recognize": lambda audio, key: deepgram_transcribe(audio, key)}
}

# 电台列表
stations = [
    {"name": "BBC World Service", "description": "新闻/谈话", "country": "英国 (UK)", "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service", "format": "MP3"},
    {"name": "NPR Program Stream", "description": "新闻/综合", "country": "美国 (USA)", "url": "https://npr-ice.streamguys1.com/live.mp3", "format": "MP3"},
    {"name": "KEXP Radio", "description": "另类/独立音乐", "country": "美国 (USA)", "url": "https://kexp-mp3-128.streamguys1.com/kexp128.mp3", "format": "MP3"},
    {"name": "Radio Paradise (Main Mix)", "description": "摇滚/多种", "country": "未知", "url": "https://stream.radioparadise.com/mp3-192", "format": "MP3"}
]

def deepgram_transcribe(audio_data, api_key):
    """
    使用Deepgram API转录音频数据
    
    参数:
        audio_data: 二进制音频数据
        api_key: Deepgram API密钥
        
    返回:
        转录的文本字符串
    """
    dg_connection = deepgram.listen.websocket.v("1")
    transcript = []
    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if sentence:
            transcript.append(sentence)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    options = LiveOptions(model="nova-3")
    if not dg_connection.start(options):
        raise Exception("Failed to start Deepgram connection")
    dg_connection.send(audio_data)
    dg_connection.finish()
    return " ".join(transcript) if transcript else ""

def record_audio():
    """
    录制麦克风音频
    
    返回:
        录制的音频数据（二进制格式）
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = [stream.read(CHUNK) for _ in range(int(RATE / CHUNK * RECORD_SECONDS))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    return b''.join(frames)

def stream_audio_transcription(url, api_key, text_container):
    """
    从音频流源进行实时语音转录
    
    参数:
        url: 音频流URL
        api_key: Deepgram API密钥
        text_container: Streamlit容器，用于显示转录文本
        
    返回:
        完整的转录文本
    """
    global transcript_global
    transcript_global = []
    # 添加一个计数器来跟踪显示的行数
    display_count = 0
    
    dg_connection = deepgram.listen.websocket.v("1")
    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if sentence:
            transcript_global.append(sentence)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    options = LiveOptions(model="nova-3", language="en-US")
    if not dg_connection.start(options):
        return "Deepgram 连接失败"

    lock_exit = threading.Lock()
    exit_flag = False
    def stream_audio():
        nonlocal exit_flag
        try:
            with httpx.stream("GET", url, timeout=None) as r:
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit_flag:
                        lock_exit.release()
                        break
                    lock_exit.release()
                    dg_connection.send(data)
        except:
            lock_exit.acquire()
            exit_flag = True
            lock_exit.release()

    # 创建并启动音频流线程
    stream_thread = threading.Thread(target=stream_audio)
    stream_thread.start()

    start_time = time.time()
    max_time = 600
    update_interval = 2
    
    # 用于存储显示的文本行
    display_lines = []
    
    while time.time() - start_time < max_time:
        if not stream_thread.is_alive():
            break
        if transcript_global:
            # 获取新的转录文本
            new_lines = transcript_global[display_count:]
            if new_lines:
                # 添加新行到显示列表
                display_lines.extend(new_lines)
                # 更新计数器
                display_count = len(transcript_global)
                
                # 如果超过10行，清空并重新开始
                if len(display_lines) > 10:
                    display_lines = display_lines[-10:]
                
                # 生成带有交替颜色的HTML显示内容
                colored_lines = []
                for i, line in enumerate(display_lines):
                    # 偶数行使用深蓝色，奇数行使用深棕色
                    color = "#1a5276" if i % 2 == 0 else "#784212"  # 深蓝色和深棕色
                    colored_lines.append(f'<div style="color:{color};">{line}</div>')
                
                html_content = "".join(colored_lines)
                text_container.markdown(f""" 
                <div id='transcript-container' class='transcript-box'> 
                <div style="font-weight:bold;">识别的文字:</div>{html_content} 
                </div> 
                <script> 
                (function() {{ 
                    var box = document.getElementById('transcript-container'); 
                    if (box) {{ 
                        box.scrollTop = box.scrollHeight; 
                    }} 
                }})(); 
                </script> 
                """, unsafe_allow_html=True)
        time.sleep(update_interval)

    # 结束音频流线程
    lock_exit.acquire()
    exit_flag = True
    lock_exit.release()
    stream_thread.join()
    dg_connection.finish()
    return " ".join(transcript_global)

def main():
    """
    Streamlit应用主函数，设置UI并处理用户交互
    """
    st.set_page_config(page_title="FM音乐源播放器", layout="wide")
    st.markdown('''
        <style>
        .transcript-box {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background-color: #f9f9f9;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 10px;
            font-size: 16px;
            scroll-behavior: smooth;
            line-height: 1.5;
        }
        </style>
    ''', unsafe_allow_html=True)

    st.title("FM音乐源播放器与实时语音转文字")
    selected = st.selectbox("选择电台", [s["name"] for s in stations])
    url = next(s["url"] for s in stations if s["name"] == selected)
    st.audio(url, format="audio/mp3", start_time=0)
    st.slider("音量", 0, 100, 50)

    if st.toggle("启用语音转文字"):
        st.write("语音转文字功能已启用")
        mode = st.radio("选择识别模式", ["音频流源", "麦克风录音"])
        service = speech_services["Deepgram"]
        if mode == "麦克风录音":
            st.write("正在监听麦克风...")
            audio = record_audio()
            try:
                text = service["recognize"](audio, service["key"])
                # 添加自动滚动到底部的JavaScript，并使用深蓝色显示文本
                st.markdown(f"""
                <div id='transcript-container' class='transcript-box'>
                <div style="font-weight:bold;">识别的文字:</div>
                <div style="color:#1a5276;">{text}</div>
                </div>
                <script>
                (function() {{
                    var box = document.getElementById('transcript-container');
                    if (box) {{
                        box.scrollTop = box.scrollHeight;
                    }}
                }})();
                </script>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.write(f"请求错误: {e}")
        else:
            st.write("正在从音频流源识别...")
            container = st.empty()
            full_text = stream_audio_transcription(url, service["key"], container)
            st.write(f"转录完成，文本长度: {len(full_text)}")

if __name__ == "__main__":
    main()