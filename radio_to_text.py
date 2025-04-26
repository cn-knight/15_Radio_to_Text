"""
FM电台播放器与实时语音转文字应用

这个应用程序实现了以下功能：
1. 播放多个网络电台音频流（MP3格式）
2. 实时将电台中的语音转为文字（Speech-to-Text）
3. 支持麦克风录音并进行语音识别
4. 使用Streamlit构建友好的Web用户界面

主要组件：
- Streamlit: 构建Web界面
- Deepgram: 提供实时语音识别服务
- httpx: 处理音频流请求
- pyaudio: 处理麦克风录音
- threading: 实现异步音频处理

作者: 基于文档中的代码创建
"""

import streamlit as st
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import httpx
import threading
import pyaudio
import wave

# 加载环境变量
load_dotenv()

# 获取API密钥
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

# 初始化语音识别器
deepgram = DeepgramClient(api_key=deepgram_api_key)

# 语音识别服务配置
speech_services = {
    "Deepgram": {"key": deepgram_api_key, "recognize": lambda audio, key: deepgram_transcribe(audio, key)}
}

def deepgram_transcribe(audio_data, api_key):
    """
    使用Deepgram API进行语音转录
    
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
        if len(sentence) > 0:
            transcript.append(sentence)

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    options = LiveOptions(model="nova-3")

    if dg_connection.start(options) is False:
        raise Exception("Failed to start Deepgram connection")

    dg_connection.send(audio_data)
    dg_connection.finish()

    return " ".join(transcript) if transcript else ""

def record_audio():
    """
    录制音频数据
    
    返回:
        录制的音频数据（二进制格式）
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5  # 可以根据需要调整录制时间

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

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
    dg_connection = deepgram.listen.websocket.v("1")
    transcript = []

    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) > 0:
            transcript.append(sentence)
            print(f"Received transcript: {sentence}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    options = LiveOptions(model="nova-3")

    if dg_connection.start(options) is False:
        raise Exception("Failed to start Deepgram connection")

    lock_exit = threading.Lock()
    exit_flag = False

    def stream_audio():
        nonlocal exit_flag
        try:
            with httpx.stream("GET", url, timeout=None) as r:
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit_flag:
                        break
                    lock_exit.release()
                    dg_connection.send(data)
                    print(">", end="", flush=True)
        except Exception as e:
            print(f"Stream audio error: {e}")
            lock_exit.acquire()
            exit_flag = True
            lock_exit.release()

    # 创建并启动音频流线程
    stream_thread = threading.Thread(target=stream_audio)
    stream_thread.start()

    # 持续转录，直到用户手动停止或达到最大转录时间（例如60秒）
    import time
    max_transcription_time = 600  # 最大转录时间（秒）
    start_time = time.time()
    update_interval = 2  # 每2秒更新一次UI
    last_update_time = start_time

    # 修复：移除对session_state的引用，恢复原始逻辑
    while time.time() - start_time < max_transcription_time:
        if not stream_thread.is_alive():
            break
        current_time = time.time()
        if current_time - last_update_time >= update_interval and transcript:
            text_container.write("识别的文字: " + " ".join(transcript))
            last_update_time = current_time
        time.sleep(1)  # 每秒检查一次

    # 结束音频流线程
    lock_exit.acquire()
    exit_flag = True
    lock_exit.release()

    stream_thread.join()
    dg_connection.finish()
    print("\nTranscription finished. Final transcript:", " ".join(transcript))

    return " ".join(transcript) if transcript else "未识别到内容"

# 电台列表
stations = [
    {"name": "BBC World Service", "description": "新闻/谈话", "country": "英国 (UK)", "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service", "format": "MP3"},
    {"name": "NPR Program Stream", "description": "新闻/综合", "country": "美国 (USA)", "url": "https://npr-ice.streamguys1.com/live.mp3", "format": "MP3"},
    {"name": "KEXP Radio", "description": "另类/独立音乐", "country": "美国 (USA)", "url": "https://kexp-mp3-128.streamguys1.com/kexp128.mp3", "format": "MP3"},
    {"name": "Radio Paradise (Main Mix)", "description": "摇滚/多种", "country": "未知", "url": "https://stream.radioparadise.com/mp3-192", "format": "MP3"}
]

# Streamlit应用主函数
def main():
    """
    Streamlit应用主函数，设置UI并处理用户交互
    """
    # Streamlit应用标题
    st.title("FM音乐源播放器")

    # 选择电台
    selected_station = st.selectbox("选择电台", [station["name"] for station in stations])
    station_url = next(station["url"] for station in stations if station["name"] == selected_station)

    # 播放音频
    st.audio(station_url, format="audio/mp3", start_time=0)

    # 音量控制
    volume = st.slider("音量", 0, 100, 50)
    st.write(f"当前音量: {volume}%")

    # 功能开关
    speech_to_text_enabled = st.toggle("启用语音转文字")

    # 语音转文字
    # 语音转文字
    if speech_to_text_enabled:
        st.write("语音转文字功能已启用")
        recognition_mode = st.radio("选择识别模式", ["音频流源", "麦克风录音"])
        service_provider = "Deepgram"  # 固定使用Deepgram服务
        service = speech_services[service_provider]
    
        if recognition_mode == "麦克风录音":
            st.write("正在监听麦克风...")
            audio_data = record_audio()
            try:
                text = service["recognize"](audio_data, service["key"])
                st.write("识别的文字:", text)
            except Exception as e:
                st.write(f"请求错误: {e}")
        else:  # 音频流源
            st.write("正在从音频流源识别...")
            try:
                text_container = st.empty()  # 用于动态更新文本的容器
                # 移除停止按钮和相关逻辑
                full_text = stream_audio_transcription(station_url, service["key"], text_container)
                text_container.write("识别的文字: " + full_text)
            except Exception as e:
                st.write(f"请求错误: {e}")

    # 页面底部信息
    st.write("这是一个用于学习英语的FM音乐源播放器，支持实时语音转文字功能。")

# 运行Streamlit应用
if __name__ == "__main__":
    main()