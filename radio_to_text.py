"""
FM音乐源播放器与实时语音转文字应用
该脚本实现了一个基于Streamlit的FM电台播放器，集成了语音转文字功能。
主要功能：播放多个在线电台、录制麦克风音频、实时转录音频流内容，并在UI中展示转录结果。
优化了内存管理，防止长时间运行导致内存泄漏。
"""

import streamlit as st
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import httpx
import threading
import pyaudio
import time
from collections import deque  # 新增：用于限制存储数据量

from openai import OpenAI

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

# 加载环境变量并初始化Deepgram客户端
load_dotenv()
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
deepgram = DeepgramClient(api_key=deepgram_api_key)

# 定义语音服务
speech_services = {
    "Deepgram": {"key": deepgram_api_key, "recognize": lambda audio, key: deepgram_transcribe(audio, key)}
}

# 电台列表，需要找到后缀是MP3或AAC格式的电台url
stations = [
    {"name": "WBEZ Chicago", "description": "新闻/综合", "country": "美国 (USA)", "url": "https://stream.wbez.org/wbez64-web.aac", "format": "AAC"},
    {"name": "NPR Program Stream", "description": "新闻/综合", "country": "美国 (USA)", "url": "https://npr-ice.streamguys1.com/live.mp3", "format": "MP3"},
    {"name": "BBC World Service", "description": "新闻/谈话", "country": "英国 (UK)", "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service", "format": "MP3"},
    {"name": "KEXP Radio", "description": "另类/独立音乐", "country": "美国 (USA)", "url": "https://kexp-mp3-128.streamguys1.com/kexp128.mp3", "format": "MP3"},
    {"name": "Radio Paradise (Main Mix)", "description": "摇滚/多种", "country": "未知", "url": "https://stream.radioparadise.com/mp3-192", "format": "MP3"},
    {"name": "KLAA Sports", "description": "体育广播", "country": "美国 (USA)", "url": "http://klaa.streamguys1.com/live", "format": "MP3"}
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

def stream_audio_transcription(url, api_key, text_container, summary_container=None):
    """
    从音频流源进行实时语音转录
    
    参数:
        url: 音频流URL
        api_key: Deepgram API密钥
        text_container: Streamlit容器，用于显示转录文本
        
    返回:
        最近的转录文本（有限长度）
    """
    # 使用deque替代无限增长的列表，限制最大长度为300条记录
    # 这样可以防止内存无限增长
    max_transcript_length = 300
    transcript_global = deque(maxlen=max_transcript_length)
    
    # 添加一个计数器来跟踪全局序号
    global_line_counter = 0
    
    dg_connection = deepgram.listen.websocket.v("1")
    def on_message(self, result, **kwargs):
        nonlocal global_line_counter
        sentence = result.channel.alternatives[0].transcript
        if sentence:
            # 为每条新的转录文本分配一个唯一的序号
            global_line_counter += 1
            # 将序号与文本一起存储到限长队列中
            transcript_global.append((global_line_counter, sentence))
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    options = LiveOptions(model="nova-3", language="en-US")
    if not dg_connection.start(options):
        return "Deepgram 连接失败"

    lock_exit = threading.Lock()
    exit_flag = False
    
    # 限制音频数据缓冲区大小
    max_buffer_size = 1024 * 1024  # 1MB 缓冲区限制
    def stream_audio():
        nonlocal exit_flag
        try:
            with httpx.stream("GET", url, timeout=None) as r:
                buffer_size = 0
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit_flag:
                        lock_exit.release()
                        break
                    lock_exit.release()
                    
                    # 发送数据到Deepgram
                    dg_connection.send(data)
                    
                    # 累计缓冲区大小
                    buffer_size += len(data)
                    # 当缓冲区达到限制时重置
                    if buffer_size > max_buffer_size:
                        buffer_size = 0
        except Exception as e:
            print(f"音频流错误: {e}")
            lock_exit.acquire()
            exit_flag = True
            lock_exit.release()

    # 创建并启动音频流线程
    stream_thread = threading.Thread(target=stream_audio)
    stream_thread.start()

    start_time = time.time()
    max_time = 600  # 最大运行10分钟
    update_interval = 2

    # 用于定时抓取文本
    last_summary_time = start_time
    summary_text = ""
    display_count = 0
    last_transcript_index = 0
    
    # 存储最近的总结，限制数量
    recent_summaries = deque(maxlen=5)  # 只保留最近5条总结

    while time.time() - start_time < max_time:
        if not stream_thread.is_alive():
            break
            
        # 检查是否有新的转录文本
        if len(transcript_global) > display_count:
            # 获取新的转录文本，只显示最新的10行
            display_lines = list(transcript_global)[-10:]
            
            # 更新计数器
            display_count = len(transcript_global)
            
            # 生成带有交替颜色的HTML显示内容
            colored_lines = []
            for i, (line_num, line) in enumerate(display_lines):
                color = "#1a5276" if line_num % 2 == 0 else "#784212"
                line_with_number = f'<span style="font-weight:bold; font-size:1.2em; margin-right:8px;">{line_num}</span> {line}'
                colored_lines.append(f'<div style="color:{color};">{line_with_number}</div>')
            
            html_content = "".join(colored_lines)
            text_container.markdown(f""" 
            <div id='transcript-container' class='transcript-box'> 
            {html_content} 
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
            
        # 每隔20秒抓取一次"新增"的转录文本
        if time.time() - last_summary_time >= 20:
            # 只处理自上次总结以来的新内容
            new_lines = list(transcript_global)[last_transcript_index:]
            current_text = " ".join([text for _, text in new_lines])
            
            # 恢复控制台输出日志
            print("【20秒抓取的转录文本】", current_text)
            
            # 更新索引，避免重复处理
            last_transcript_index = len(transcript_global)
            
            # 调用DeepSeek API
            try:
                if current_text.strip():  # 只有有新内容时才调用
                    response = deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system",
                            "content": (
                                "你收到的文字是我随机在一个英语广播电台获取的内容文本，我需要你用简洁的中文段落总结电台正在说什么。"
                                "不要使用Markdown格式，不要加空行，不要编号或列表，只需直接输出总结内容。"
                                "不需要逐句翻译，而是尽可能高度总结。"
                                "因为内容有限，以及转录质量，有些词汇可能不准确，你要依据文本上下文进行合理猜测。"
                            )
                        },
                        {"role": "user", "content": current_text}
                        ],
                        stream=False
                    )
                    summary_text = response.choices[0].message.content
                    # 存储最近的总结
                    recent_summaries.append(summary_text)
                    # 恢复控制台输出日志
                    print("【AI总结内容】", summary_text)
            except Exception as e:
                summary_text = f"AI总结失败: {e}"
                # 恢复错误日志输出
                print(f"【AI总结错误】: {e}")
            
            if summary_container is not None:
                summary_container.markdown(f"""
                <div class='transcript-box' style='margin-top:10px; height:18vh; font-size:15px;'>
                    {summary_text}
                </div>
                """, unsafe_allow_html=True)
                
            last_summary_time = time.time()
            
        time.sleep(update_interval)

    # 结束音频流线程
    lock_exit.acquire()
    exit_flag = True
    lock_exit.release()
    stream_thread.join()
    dg_connection.finish()
    
    # 返回最近的转录文本（不包含序号），而不是全部历史
    return " ".join([text for _, text in list(transcript_global)[-50:]])

def main():
    """
    Streamlit应用主函数，设置UI并处理用户交互
    """
    st.set_page_config(
        page_title="FM音乐源播放器", 
        layout="centered",  # 改为centered布局，更适合移动设备
        initial_sidebar_state="collapsed"  # 默认收起侧边栏，为移动设备提供更多空间
    )
    
    # 添加移动端友好的CSS样式
    st.markdown('''
        <style>
        /* 强制应用9:16比例的容器样式，不使用媒体查询，使其在所有设备上生效 */
        .main .block-container {
            max-width: 450px !important;  /* 控制最大宽度 */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin: 0 auto;
        }
        
        /* 设置内容区域的高度，实现9:16比例 */
        .stApp {
            height: 100vh;
        }
        
        .main {
            height: 100%;
        }
        
        /* 调整标题位置，向上移动 */
        h1:first-child {
            margin-top: -20px !important;  /* 负值使标题向上移动 */
            padding-top: 0 !important;
        }
        
        /* 调整选择框位置，增加与标题的距离 */
        .stSelectbox {
            margin-top: 5px !important;  /* 正值增加与标题的距离 */
        }
        
        /* 调整文本框样式 */
        .transcript-box {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background-color: #f9f9f9;
            height: 40vh;  /* 使用视口高度的百分比 */
            overflow-y: auto;
            margin-bottom: 10px;
            font-size: 16px;
            scroll-behavior: smooth;
            line-height: 1.5;
        }
        
        /* 调整按钮和控件大小，适合触摸操作 */
        .stButton>button {
            font-size: 1.2rem;
            padding: 0.5rem 1rem;
            height: auto;
        }
        
        /* 调整音频播放器大小 */
        audio {
            width: 100%;
        }
        
        /* 调整标题大小 */
        h1 {
            font-size: 1.8rem !important;
        }
        
        /* 调整选择框和滑块大小 */
        .stSelectbox, .stSlider {
            margin-bottom: 0.5rem;
        }
        </style>
    ''', unsafe_allow_html=True)
    
    st.title("Joying FM-英文实时广播内容识别")
    
    # 移除音量控制相关的列布局和控件
    # 原来的列布局代码:
    # col1, col2 = st.columns([3, 1])
    # 
    # with col1:
    #     selected = st.selectbox("选择电台", [s["name"] for s in stations])
    #     url = next(s["url"] for s in stations if s["name"] == selected)
    #     st.audio(url, format="audio/mp3", start_time=0)
    # 
    # with col2:
    #     st.slider("音量", 0, 100, 50) # 音量控制控件被移除

    # 选择电台和音频播放器将垂直排列，并占据可用宽度
    selected = st.selectbox("电台选择", [s["name"] for s in stations], label_visibility="collapsed")  # 提供标签但隐藏它
    url = next(s["url"] for s in stations if s["name"] == selected)
    st.audio(url, format="audio/mp3", start_time=0) # 音频将以默认最大音量播放
    
    if st.toggle("几秒后文字将出现在下方", value=True):
        service = speech_services["Deepgram"]
        container = st.empty()
        container.markdown("""
        <div id='transcript-container' class='transcript-box'>
        <!-- 这里将显示识别的文字 -->
        </div>
        """, unsafe_allow_html=True)
        # 新增：用于显示AI总结的容器，并提前渲染空框
        summary_container = st.empty()
        summary_container.markdown("""
        <div class='transcript-box' style='margin-top:10px; height:18vh; font-size:15px;'>
            <span style='color:#888;'>等待AI总结...</span>
        </div>
        """, unsafe_allow_html=True)
        # 调用音频流转录函数，传入summary_container
        full_text = stream_audio_transcription(url, service["key"], container, summary_container)
        # 转录完成后，不再显示完成信息
        # st.write(f"转录完成，文本长度: {len(full_text)}") # 移除这行提示文字
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()